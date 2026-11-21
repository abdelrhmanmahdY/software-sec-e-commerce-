from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from carts.models import Cart
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

        if not cart.items.exists():
            return Response({"error": "Cart has no items"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user, status="Pending")

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart.items.all().delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
