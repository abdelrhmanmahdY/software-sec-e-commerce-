import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import Cart, CartItem


class CartQuantityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cart_user", password="Disposable-Test-123!")
        self.category = Category.objects.create(name="Cart tests")
        self.product = Product.objects.create(
            name="Limited stock item",
            category=self.category,
            price=Decimal("10.00"),
            stock=2,
        )
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def test_add_uses_requested_quantity_and_rejects_over_stock(self):
        first = self.api.post(
            "/api/carts/cart/add/",
            {"product": self.product.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["quantity"], 1)

        second = self.api.post(
            "/api/carts/cart/add/",
            {"product": self.product.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["quantity"], 2)

        over_stock = self.api.post(
            "/api/carts/cart/add/",
            {"product": self.product.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(over_stock.status_code, 400)
        self.assertEqual(
            CartItem.objects.get(
                cart__user=self.user,
                product=self.product,
            ).quantity,
            2,
        )

    def test_storefront_add_uses_same_stock_limit(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/dashboard/shop/",
            {"product_id": self.product.pk, "quantity": 2},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            CartItem.objects.get(
                cart__user=self.user,
                product=self.product,
            ).quantity,
            2,
        )

    def test_missing_item_id_returns_validation_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/carts/cart/update-quantity/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "item_id is required.")

    def test_quantity_update_rejects_stock_excess_without_mutating_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/carts/cart/update-quantity/",
            data=json.dumps({"item_id": item.pk, "quantity": 3}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
