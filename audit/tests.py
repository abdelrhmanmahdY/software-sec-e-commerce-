from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order
from products.models import Category, Product
from users.totp import get_totp_code

from .models import AuditLog

PW = "Str0ng-Passw0rd!"


def make_user(name, staff=False):
    return User.objects.create_user(name, f"{name}@example.com", PW, is_staff=staff)


@override_settings(LOGIN_MAX_FAILURES=3, LOGIN_MAX_FAILURES_PER_IP=50)
class AuthenticationTests(TestCase):
    def setUp(self):
        make_user("alice")

    def test_successful_login_is_logged(self):
        self.client.post(reverse("login"), {"username": "alice", "password": PW})
        self.assertTrue(AuditLog.objects.filter(action="login_success", username="alice").exists())

    def test_lockout_after_repeated_failures_even_with_right_password(self):
        for _ in range(3):
            self.client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        self.assertEqual(AuditLog.objects.filter(action="login_failed", username="alice").count(), 3)
        resp = self.client.post(reverse("login"), {"username": "alice", "password": PW})
        self.assertNotIn("_auth_user_id", self.client.session)      # correct password refused
        self.assertContains(resp, "Too many failed attempts")
        self.assertTrue(AuditLog.objects.filter(action="login_locked").exists())

    def test_lockout_is_per_ip_so_a_victim_is_not_locked_from_elsewhere(self):
        for _ in range(3):
            self.client.post(reverse("login"), {"username": "alice", "password": "x"}, REMOTE_ADDR="6.6.6.6")
        self.client.post(reverse("login"), {"username": "alice", "password": PW}, REMOTE_ADDR="7.7.7.7")
        self.assertIn("_auth_user_id", self.client.session)

    def test_jwt_login_lockout_returns_429_and_success_is_logged(self):
        api = APIClient()
        ok = api.post("/api/auth/login/", {"username": "alice", "password": PW}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="login_success", username="alice").exists())
        for _ in range(3):
            api.post("/api/auth/login/", {"username": "alice", "password": "bad"}, format="json")
        locked = api.post("/api/auth/login/", {"username": "alice", "password": PW}, format="json")
        self.assertEqual(locked.status_code, 429)

    def test_jwt_login_requires_a_fresh_totp_code_for_enrolled_users(self):
        user = User.objects.get(username="alice")
        user.profile.totp_enabled = True
        user.profile.totp_secret = "JBSWY3DPEHPK3PXP"
        user.profile.save(update_fields=["totp_enabled", "totp_secret"])
        api = APIClient()

        missing_code = api.post(
            "/api/auth/login/",
            {"username": "alice", "password": PW},
            format="json",
        )
        self.assertEqual(missing_code.status_code, 401)
        self.assertNotIn("access", missing_code.data)

        valid_code = get_totp_code(user.profile.totp_secret)
        invalid_code = "000000" if valid_code != "000000" else "000001"
        wrong_code = api.post(
            "/api/auth/login/",
            {"username": "alice", "password": PW, "totp_code": invalid_code},
            format="json",
        )
        self.assertEqual(wrong_code.status_code, 401)
        self.assertNotIn("access", wrong_code.data)

        valid_login = api.post(
            "/api/auth/login/",
            {"username": "alice", "password": PW, "totp_code": valid_code},
            format="json",
        )
        self.assertEqual(valid_login.status_code, 200, valid_login.data)
        protected = APIClient()
        protected.credentials(
            HTTP_AUTHORIZATION=f"Bearer {valid_login.data['access']}"
        )
        self.assertEqual(protected.get("/api/orders/orders/").status_code, 200)

        replay = APIClient().post(
            "/api/auth/login/",
            {"username": "alice", "password": PW, "totp_code": valid_code},
            format="json",
        )
        self.assertEqual(replay.status_code, 401)
        self.assertNotIn("access", replay.data)

    def test_jwt_logout_blacklists_refresh_token(self):
        api = APIClient()
        tokens = api.post("/api/auth/login/", {"username": "alice", "password": PW}, format="json").json()
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(api.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code, 205)
        again = APIClient().post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(again.status_code, 401)


class AuthorizationTests(TestCase):
    def setUp(self):
        self.alice, self.bob, self.admin = make_user("alice"), make_user("bob"), make_user("root", staff=True)
        cat = Category.objects.create(name="Misc")
        self.product = Product.objects.create(name="Mug", price=Decimal("10.00"), stock=5, category=cat)
        self.order = Order.objects.create(user=self.bob)

    def api(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_customer_cannot_see_or_edit_someone_elses_order(self):
        c = self.api(self.alice)
        self.assertEqual(c.get(f"/api/orders/orders/{self.order.id}/").status_code, 404)
        self.assertEqual(c.get("/api/orders/orders/").json()["count"], 0)
        # a customer is refused (403) before the object is even looked up
        self.assertEqual(c.patch(f"/api/orders/orders/{self.order.id}/", {"status": "Completed"}, format="json").status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Pending")

    def test_customer_cannot_modify_or_delete_even_own_order(self):
        own = Order.objects.create(user=self.alice)
        c = self.api(self.alice)
        self.assertEqual(c.patch(f"/api/orders/orders/{own.id}/", {"status": "Completed"}, format="json").status_code, 403)
        self.assertEqual(c.delete(f"/api/orders/orders/{own.id}/").status_code, 403)

    def test_client_supplied_price_and_status_are_ignored(self):
        resp = self.api(self.alice).post(
            "/api/orders/orders/",
            {"status": "Completed", "items": [{"product": self.product.id, "quantity": 2, "price": "0.01"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        order = Order.objects.get(pk=resp.json()["id"])
        self.assertEqual(order.status, "Pending")
        self.assertEqual(order.items.get().price, Decimal("10.00"))

    def test_staff_can_manage_orders_and_order_items_are_staff_only(self):
        self.assertEqual(self.api(self.admin).patch(f"/api/orders/orders/{self.order.id}/", {"status": "Completed", "items": []}, format="json").status_code, 200)
        self.assertEqual(self.api(self.alice).get("/api/orders/order-items/").status_code, 403)

    def test_non_staff_gets_403_on_dashboard_admin_pages_and_it_is_audited(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("users_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("audit_log")).status_code, 403)
        self.assertTrue(AuditLog.objects.filter(action="access_denied", username="alice").exists())

    def test_product_delete_requires_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("product_delete", args=[self.product.pk])).status_code, 405)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_category_ajax_is_staff_only(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("ajax_add_category"), {"name": "Hax"}).status_code, 403)

    def test_admin_cannot_change_own_role(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("user_update_role", args=[self.admin.pk]), {"role": "customer"})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff)


class AccountingTests(TestCase):
    def test_changes_record_actor_ip_and_old_new_values_but_never_passwords(self):
        admin, bob = make_user("root", staff=True), make_user("bob")
        self.client.force_login(admin)
        self.client.post(reverse("user_update_role", args=[bob.pk]), {"role": "admin"}, REMOTE_ADDR="10.1.2.3")
        log = AuditLog.objects.get(action="update", object_type="User", object_id=str(bob.pk))
        self.assertEqual(log.username, "root")
        self.assertEqual(log.ip_address, "10.1.2.3")
        self.assertEqual(log.changes["is_staff"], ["False", "True"])

        bob.set_password("An0ther-Str0ng-One!")
        bob.save()
        pw = AuditLog.objects.filter(action="update", object_type="User", changes__has_key="password").first()
        self.assertEqual(pw.changes["password"], "changed")
        self.assertNotIn("An0ther", str(AuditLog.objects.all().values()))

    def test_deleting_a_user_keeps_their_audit_trail(self):
        u = make_user("temp")
        self.client.post(reverse("login"), {"username": "temp", "password": PW})
        u.delete()
        self.assertTrue(AuditLog.objects.filter(action="login_success", username="temp", user=None).exists())

    def test_audit_page_visible_to_staff(self):
        self.client.force_login(make_user("root", staff=True))
        self.assertContains(self.client.get(reverse("audit_log")), "Audit Log")
