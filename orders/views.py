from decimal import Decimal
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from carts.models import Cart
from users.models import UserProfile
from users.permissions import IsStaff, IsStaffOrCreateReadOnly

class OrderViewSet(viewsets.ModelViewSet):
    """Customers see/create only their own orders; only staff can edit/delete."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsStaffOrCreateReadOnly]

    def get_queryset(self):
        qs = Order.objects.select_related("user").prefetch_related("items")
        user = self.request.user
        return qs if user.is_staff else qs.filter(user=user)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    def get_queryset(self):
        return OrderItem.objects.select_related("order", "product")

    def perform_create(self, serializer):
        serializer.save(price=serializer.validated_data["product"].price)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            items = list(cart.items.select_related("product").select_for_update())
            if not items:
                return Response({"error": "Cart has no items"}, status=status.HTTP_400_BAD_REQUEST)

            total = sum((item.product.price * item.quantity for item in items), Decimal("0"))
            profile = UserProfile.objects.select_for_update().filter(user=user).first()
            if profile is None or profile.store_credit < total:
                return Response({"error": "Insufficient store credit"}, status=status.HTTP_400_BAD_REQUEST)

            for item in items:
                if item.quantity > item.product.stock:
                    return Response(
                        {"error": f"Insufficient stock for {item.product.name}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            profile.store_credit -= total
            profile.save(update_fields=["store_credit"])

            order = Order.objects.create(user=user, status="Pending")
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                item.product.stock -= item.quantity
                item.product.save(update_fields=["stock"])

            cart.items.all().delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
