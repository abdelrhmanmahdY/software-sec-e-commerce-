from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
import json

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product
from orders.models import Order, OrderItem  
from users.models import Coupon



class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )
        cart_item.quantity += quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)


class RemoveFromCartView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        item.delete()
        return Response({"success": "Item removed"})


@require_POST
def UpdateCartItemQuantityView(request):
    try:
        data = json.loads(request.body)
        item_id = data.get("item_id")
        quantity = int(data.get("quantity", 1))
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if quantity < 1:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_POST
@login_required
def CheckoutView(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        data = {}

    coupon_code = str(data.get("coupon_code", "")).strip().upper()
    use_credit = bool(data.get("use_store_credit", False))

    subtotal = sum((item.product.price * item.quantity for item in cart.items.all()), Decimal("0"))
    discount = Decimal("0")
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if coupon.expires_at and coupon.expires_at < timezone.now():
                coupon = None
        except Coupon.DoesNotExist:
            coupon = None
        if coupon is None:
            return JsonResponse({"error": "Coupon is invalid or expired"}, status=400)
        discount = (subtotal * Decimal(coupon.discount_percent) / Decimal("100")).quantize(Decimal("0.01"))

    total = subtotal + Decimal("5.00") + cart.tax - discount
    if total < 0:
        total = Decimal("0")

    profile = getattr(request.user, "profile", None)
    credit_used = Decimal("0")
    if use_credit and profile:
        credit_used = min(profile.store_credit, total)
        profile.store_credit -= credit_used

    try:
        with transaction.atomic():
            for item in cart.items.select_for_update():
                if item.quantity > item.product.stock:
                    return JsonResponse({"error": f"Insufficient stock for {item.product.name}"}, status=400)

            order = Order.objects.create(user=request.user, status="Pending")

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                item.product.stock -= item.quantity
                item.product.save(update_fields=["stock"])

            if profile and credit_used:
                profile.save(update_fields=["store_credit"])

            cart.items.all().delete()

        return JsonResponse({
            "success": True,
            "message": "Checkout completed successfully!",
            "order_id": order.id,
            "subtotal": str(subtotal),
            "discount": str(discount),
            "store_credit_used": str(credit_used),
            "total": str(total),
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)