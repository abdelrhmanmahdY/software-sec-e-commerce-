from .models import CartItem


def add_cart_quantity(cart, product, quantity):
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    updated_quantity = quantity + (cart_item.quantity if cart_item else 0)
    if updated_quantity > product.stock:
        return None

    if cart_item is None:
        return CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=updated_quantity,
        )

    cart_item.quantity = updated_quantity
    cart_item.save(update_fields=["quantity"])
    return cart_item
