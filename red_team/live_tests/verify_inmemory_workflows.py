"""Verify selected SecureShop business and access controls in memory-only SQLite."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEBUG"] = "True"
os.environ["EMAIL_BACKEND"] = "django.core.mail.backends.locmem.EmailBackend"
os.environ["SECRET_KEY"] = "CET431-RedTeam-InMemory-Test-Key-Only-2026"

import django

django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client
from rest_framework.test import APIClient

from carts.models import Cart, CartItem
from orders.models import Order
from products.models import Category, Product
from users.models import Coupon, CouponUsage, NewsletterSubscriber


settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver", "localhost"]
logging.disable(logging.CRITICAL)


def main():
    parser = argparse.ArgumentParser(
        description="Run selected business-logic and access tests with no persistent database."
    )
    evidence_dir = ROOT / "red_team" / "evidence" / "review"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser.add_argument(
        "--output",
        type=Path,
        default=evidence_dir / f"workflow_checks_{stamp}.json",
        help="new evidence JSON path inside red_team/evidence/review/",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != evidence_dir.resolve():
        parser.error("output must stay inside red_team/evidence/review/")
    if output.exists():
        parser.error(f"refusing to overwrite existing evidence: {output}")

    call_command("migrate", interactive=False, verbosity=0)
    user = User.objects.create_user(
        username="rt_workflow_customer",
        email="rt_workflow_customer@example.test",
        password="Disposable-Workflow-Test-Only!",
    )
    profile = user.profile
    profile.store_credit = Decimal("1000.00")
    profile.save(update_fields=["store_credit"])
    category = Category.objects.create(name="RT workflow fixtures")
    product = Product.objects.create(
        name="Disposable test item",
        category=category,
        price=Decimal("100.00"),
        stock=2,
    )
    coupon = Coupon.objects.create(code="RT-COUPON-ONCE", discount_percent=10, active=True)
    cart = Cart.objects.create(user=user)
    client = Client(HTTP_HOST="localhost")
    client.force_login(user)
    api_client = APIClient(HTTP_HOST="localhost")
    api_client.force_authenticate(user=user)

    # Cookie-name spoofing must not create a Django-authenticated session.
    spoofed = Client(HTTP_HOST="localhost", HTTP_COOKIE="user=admin")
    profile_response = spoofed.get("/dashboard/profile/")
    admin_response = spoofed.get("/admin/users/newslettersubscriber/")
    docs_response = Client(HTTP_HOST="localhost").get("/api/docs/")
    cookie_checks = {
        "forged_cookie_request": "GET /dashboard/profile/ with user=admin cookie",
        "forged_user_cookie_profile_status": profile_response.status_code,
        "forged_user_cookie_authenticated": bool(
            getattr(getattr(profile_response, "wsgi_request", None), "user", None)
            and profile_response.wsgi_request.user.is_authenticated
        ),
        "unauthenticated_newsletter_admin_status": admin_response.status_code,
        "unauthenticated_newsletter_admin_redirect": admin_response.get("Location", ""),
        "unauthenticated_api_docs_status": docs_response.status_code,
        "unauthenticated_api_docs_denied": docs_response.status_code in (401, 403),
    }

    first_add_response = api_client.post(
        "/api/carts/cart/add/",
        data=json.dumps({"product": product.pk, "quantity": 1}),
        content_type="application/json",
    )
    overstock_add_response = api_client.post(
        "/api/carts/cart/add/",
        data=json.dumps({"product": product.pk, "quantity": 2}),
        content_type="application/json",
    )
    if first_add_response.status_code not in (200, 201):
        raise AssertionError(
            f"Cart add failed with HTTP {first_add_response.status_code}: "
            f"{first_add_response.content.decode('utf-8', 'replace')[:500]}"
        )
    cart.refresh_from_db()
    cart_item = CartItem.objects.get(cart=cart, product=product)
    credit_before_overstock_add = profile.store_credit
    stock_before_overstock_add = product.stock
    orders_before_overstock_add = Order.objects.count()
    profile.refresh_from_db()
    product.refresh_from_db()
    cart.refresh_from_db()
    stock_checks = {
        "first_cart_add_request": {"product": product.pk, "quantity": 1},
        "first_cart_add_status": first_add_response.status_code,
        "first_cart_add_response": first_add_response.content.decode("utf-8", "replace"),
        "first_cart_item_quantity": cart_item.quantity,
        "overstock_add_request": {"product": product.pk, "quantity": 2},
        "overstock_add_status": overstock_add_response.status_code,
        "overstock_add_response": overstock_add_response.content.decode("utf-8", "replace"),
        "overstock_add_rejected": overstock_add_response.status_code == 400,
        "cart_quantity_unchanged_after_rejection": cart_item.quantity == 1,
        "stock_unchanged_after_rejection": product.stock == stock_before_overstock_add,
        "credit_unchanged_after_rejection": profile.store_credit == credit_before_overstock_add,
        "orders_unchanged_after_rejection": Order.objects.count() == orders_before_overstock_add,
        "cart_retained_after_rejection": cart.items.filter(pk=cart_item.pk).exists(),
    }
    if (
        first_add_response.status_code not in (200, 201)
        or first_add_response.json().get("quantity") != 1
        or not stock_checks["overstock_add_rejected"]
        or not stock_checks["cart_quantity_unchanged_after_rejection"]
        or not stock_checks["stock_unchanged_after_rejection"]
        or not stock_checks["credit_unchanged_after_rejection"]
        or not stock_checks["orders_unchanged_after_rejection"]
        or not stock_checks["cart_retained_after_rejection"]
    ):
        raise AssertionError(f"Unexpected stock workflow response: {stock_checks}")

    # Missing item identifiers are validation errors, not object-not-found errors.
    empty_object_response = client.post(
        "/api/carts/cart/update-quantity/",
        data=json.dumps({}),
        content_type="application/json",
    )
    empty_body_response = client.post(
        "/api/carts/cart/update-quantity/",
        data="",
        content_type="application/json",
    )
    empty_input_checks = {
        "empty_object_request": "{}",
        "empty_object_status": empty_object_response.status_code,
        "empty_object_error": empty_object_response.json().get("error"),
        "empty_object_content_type": empty_object_response.get("Content-Type", ""),
        "empty_body_request": "",
        "empty_body_status": empty_body_response.status_code,
        "empty_body_content_type": empty_body_response.get("Content-Type", ""),
    }
    if (
        empty_object_response.status_code != 400
        or empty_input_checks["empty_object_error"] != "item_id is required."
        or empty_body_response.status_code != 400
    ):
        raise AssertionError(f"Unexpected missing-field validation responses: {empty_input_checks}")

    # Valid one-item checkout uses disposable credit and records the actual deltas.
    profile.store_credit = Decimal("200.00")
    profile.save(update_fields=["store_credit"])
    before_credit = profile.store_credit
    before_stock = product.stock
    before_orders = Order.objects.count()
    checkout_response = client.post(
        "/api/carts/orders/checkout/",
        data=json.dumps({"coupon_code": coupon.code, "use_store_credit": True}),
        content_type="application/json",
    )
    profile.refresh_from_db()
    product.refresh_from_db()
    coupon_usage = CouponUsage.objects.filter(user=user, coupon=coupon).count()
    first_order = Order.objects.filter(user=user).order_by("-id").first()
    first_checkout = {
        "status": checkout_response.status_code,
        "request": {"coupon_code": coupon.code, "use_store_credit": True},
        "response": checkout_response.content.decode("utf-8", "replace"),
        "order_created": Order.objects.count() == before_orders + 1,
        "coupon_usage_count": coupon_usage,
        "store_credit_before": str(before_credit),
        "store_credit_after": str(profile.store_credit),
        "stock_before": before_stock,
        "stock_after": product.stock,
        "order_total": checkout_response.json().get("total"),
        "stored_item_price": str(first_order.items.first().price) if first_order and first_order.items.exists() else None,
    }
    if checkout_response.status_code != 200 or coupon_usage != 1:
        raise AssertionError(f"Expected first coupon redemption to succeed: {first_checkout}")

    # A repeat redemption must leave credit, stock, orders, and cart unchanged.
    add_again = api_client.post(
        "/api/carts/cart/add/",
        data=json.dumps({"product": product.pk, "quantity": 1}),
        content_type="application/json",
    )
    replay_credit = profile.store_credit
    replay_stock = product.stock
    replay_orders = Order.objects.count()
    replay_response = client.post(
        "/api/carts/orders/checkout/",
        data=json.dumps({"coupon_code": coupon.code, "use_store_credit": True}),
        content_type="application/json",
    )
    profile.refresh_from_db()
    product.refresh_from_db()
    cart.refresh_from_db()
    coupon_replay_checks = {
        "add_second_cart_item_status": add_again.status_code,
        "add_second_cart_item_request": {"product": product.pk, "quantity": 1},
        "add_second_cart_item_response": add_again.content.decode("utf-8", "replace"),
        "repeat_coupon_status": replay_response.status_code,
        "repeat_coupon_request": {"coupon_code": coupon.code, "use_store_credit": True},
        "repeat_coupon_response": replay_response.content.decode("utf-8", "replace"),
        "repeat_coupon_rejected": replay_response.status_code == 400,
        "credit_unchanged": profile.store_credit == replay_credit,
        "stock_unchanged": product.stock == replay_stock,
        "orders_unchanged": Order.objects.count() == replay_orders,
        "cart_retained_after_rejection": cart.items.exists(),
    }
    if not coupon_replay_checks["repeat_coupon_rejected"]:
        raise AssertionError(f"Expected coupon replay to be rejected: {coupon_replay_checks}")

    # H4 retest: generated coupon values should not reveal a short sequential number.
    newsletter_codes = []
    newsletter_statuses = []
    for index in range(4):
        response = Client(HTTP_HOST="localhost").post(
            "/dashboard/newsletter/signup/",
            data=json.dumps({"email": f"rt_newsletter_{index}@example.test"}),
            content_type="application/json",
        )
        newsletter_statuses.append(response.status_code)
        if response.status_code == 200:
            newsletter_codes.append(response.json().get("coupon_code", ""))
    newsletter_checks = {
        "response_statuses": newsletter_statuses,
        "issued_count": len(newsletter_codes),
        "unique_count": len(set(newsletter_codes)),
        "random_token_format": all(
            len(code) == 17 and code.startswith("NEWS-") for code in newsletter_codes
        ),
        "subscriber_rows": NewsletterSubscriber.objects.filter(email__startswith="rt_newsletter_").count(),
    }
    newsletter_response = Client(HTTP_HOST="localhost").post(
        "/dashboard/newsletter/signup/",
        data=json.dumps({"email": "rt_newsletter_evidence@example.test"}),
        content_type="application/json",
    )
    newsletter_body = newsletter_response.json() if newsletter_response.status_code == 200 else {}
    if "coupon_code" in newsletter_body:
        newsletter_body["coupon_code"] = "[REDACTED: synthetic in-memory coupon]"

    # CSRF behavior is checked with a synthetic session and explicit enforcement.
    csrf_client = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
    csrf_client.force_login(user)
    csrf_response = csrf_client.post(
        "/dashboard/settings/",
        data={"first_name": "Changed", "last_name": "Name"},
    )
    csrf_checks = {
        "request": {"first_name": "Changed", "last_name": "Name"},
        "post_without_csrf_status": csrf_response.status_code,
        "post_without_csrf_rejected": csrf_response.status_code == 403,
        "profile_first_name_after": User.objects.get(pk=user.pk).first_name,
        "response": csrf_response.content.decode("utf-8", "replace")[:200],
    }

    result = {
        "environment": "Django TestClient; SQLite :memory:; locmem mail; synthetic account and fixtures",
        "cookie_and_admin": cookie_checks,
        "empty_input": empty_input_checks,
        "cart_quantity_and_stock": stock_checks,
        "store_credit_checkout": first_checkout,
        "coupon_replay": coupon_replay_checks,
        "newsletter_coupon_generation": newsletter_checks,
        "newsletter_redacted_response": {
            "status": newsletter_response.status_code,
            "body": newsletter_body,
        },
        "csrf": csrf_checks,
        "persistent_database_touched": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"Evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
