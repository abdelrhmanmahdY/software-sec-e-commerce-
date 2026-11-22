from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from carts.models import Cart, CartItem
from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import Coupon, NewsletterSubscriber


class Command(BaseCommand):
    help = "Seed sample users and data for every project table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing project model records before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        import os

        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "")
        staff_password = os.getenv("SEED_STAFF_PASSWORD", "")
        customer_password = os.getenv("SEED_CUSTOMER_PASSWORD", "")
        if not all((admin_password, staff_password, customer_password)):
            raise CommandError(
                "Set SEED_ADMIN_PASSWORD, SEED_STAFF_PASSWORD, and "
                "SEED_CUSTOMER_PASSWORD before seeding demo accounts."
            )

        if options["clear"]:
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(username__in=["admin", "customer", "staff"]).delete()
            NewsletterSubscriber.objects.all().delete()
            Coupon.objects.all().delete()

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Default",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = "admin@example.com"
        admin.first_name = "Default"
        admin.last_name = "Administrator"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(admin_password)
        admin.save()

        staff, _ = User.objects.get_or_create(
            username="staff",
            defaults={"email": "staff@example.com", "first_name": "Store", "last_name": "Staff", "is_staff": True},
        )
        staff.email = "staff@example.com"
        staff.first_name = "Store"
        staff.last_name = "Staff"
        staff.is_staff = True
        staff.is_superuser = False
        staff.set_password(staff_password)
        staff.save()

        customer, _ = User.objects.get_or_create(
            username="customer",
            defaults={"email": "customer@example.com", "first_name": "Example", "last_name": "Customer"},
        )
        customer.email = "customer@example.com"
        customer.first_name = "Example"
        customer.last_name = "Customer"
        customer.is_staff = False
        customer.is_superuser = False
        customer.set_password(customer_password)
        customer.save()

        # Seed store credit balance
        admin.profile.store_credit = Decimal("500.00")
        admin.profile.save(update_fields=["store_credit"])
        customer.profile.store_credit = Decimal("500.00")
        customer.profile.save(update_fields=["store_credit"])

        categories = {}
        category_rows = [
            ("Electronics", "Phones, computers, and electronic accessories"),
            ("Fashion", "Clothing, shoes, and accessories"),
            ("Home", "Furniture and household essentials"),
        ]
        for name, description in category_rows:
            category, _ = Category.objects.update_or_create(
                name=name,
                defaults={"description": description},
            )
            categories[name] = category

        product_rows = [
            ("Wireless Headphones", "Noise-cancelling Bluetooth headphones", "129.99", 25, "Electronics", "SoundMax", "0.35"),
            ("Smartphone", "128 GB unlocked smartphone", "599.99", 12, "Electronics", "TechNova", "0.18"),
            ("Running Shoes", "Lightweight everyday running shoes", "89.50", 40, "Fashion", "Sprint", "0.80"),
            ("Desk Lamp", "Adjustable LED desk lamp", "34.99", 30, "Home", "BrightHome", "1.20"),
        ]
        products = {}
        for name, description, price, stock, category_name, brand, weight in product_rows:
            product, _ = Product.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "price": Decimal(price),
                    "stock": stock,
                    "category": categories[category_name],
                    "brand": brand,
                    "weight": Decimal(weight),
                    "is_active": True,
                },
            )
            products[name] = product

        cart = Cart.objects.filter(user=customer).first()
        if cart is None:
            cart = Cart.objects.create(user=customer, tax=Decimal("4.50"))
        cart.tax = Decimal("4.50")
        cart.save()
        CartItem.objects.update_or_create(cart=cart, product=products["Wireless Headphones"], defaults={"quantity": 1})
        CartItem.objects.update_or_create(cart=cart, product=products["Running Shoes"], defaults={"quantity": 2})

        order = Order.objects.filter(user=customer, status="Processing").first()
        if order is None:
            order = Order.objects.create(user=customer, status="Processing")
        OrderItem.objects.update_or_create(
            order=order,
            product=products["Smartphone"],
            defaults={"quantity": 1, "price": Decimal("599.99")},
        )
        OrderItem.objects.update_or_create(
            order=order,
            product=products["Desk Lamp"],
            defaults={"quantity": 2, "price": Decimal("34.99")},
        )

        Coupon.objects.update_or_create(
            code="SUMMER2026",
            defaults={"discount_percent": 10, "active": True, "expires_at": None},
        )

        NewsletterSubscriber.objects.update_or_create(
            email="subscriber1@example.com",
            defaults={"coupon_code": "SUMMER2026"},
        )
        NewsletterSubscriber.objects.update_or_create(
            email="subscriber2@example.com",
            defaults={"coupon_code": "SUMMER2026"},
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))
        self.stdout.write("  demo accounts created; passwords come from SEED_*_PASSWORD environment variables")
