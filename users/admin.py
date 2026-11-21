from django.contrib import admin

from .models import Coupon, NewsletterSubscriber, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "store_credit", "email_confirmed")
    list_editable = ("store_credit", "email_confirmed")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "active", "expires_at")
    list_filter = ("active",)
    search_fields = ("code",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "coupon_code", "subscribed_at")
    search_fields = ("email", "coupon_code")
