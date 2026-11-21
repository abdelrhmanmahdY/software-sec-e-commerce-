from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem
from carts.models import Cart, CartItem
from products.serializers import ProductSerializer
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']
        read_only_fields = ['price']                 # never trust a client-supplied price
        extra_kwargs = {'quantity': {'min_value': 1}}

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'created_at', 'updated_at', 'items', 'total_price']
        read_only_fields = ['user']

    def get_total_price(self, obj):
        total = sum(item.price * item.quantity for item in obj.items.all())
        return Decimal(total).quantize(Decimal("0.01"))

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        user = self.context['request'].user
        if not user.is_staff:
            validated_data.pop('status', None)       # customers cannot pick a status
        order = Order.objects.create(user=user, **validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, price=item_data['product'].price, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, price=item_data['product'].price, **item_data)
        return instance
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']