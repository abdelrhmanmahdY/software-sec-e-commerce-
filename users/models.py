from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    store_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    email_confirmed = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    totp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(default=10)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.code


class CouponUsage(models.Model):
    """Tracks per-user coupon redemptions to prevent replay/reuse."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupon_usages")
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "coupon"], name="unique_user_coupon_usage")
        ]

    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    coupon_code = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.email


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
