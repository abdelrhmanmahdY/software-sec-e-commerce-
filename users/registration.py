from django.core import signing
from django.core.mail import send_mail


def create_unconfirmed_user(request, form):
    user = form.save(commit=False)
    user.is_active = False
    user.save()

    token = signing.dumps(user.pk, salt="account-confirmation")
    confirmation_url = request.build_absolute_uri(
        f"/dashboard/confirm/{token}/"
    )
    send_mail(
        "Confirm your account",
        f"Hi {user.first_name or user.username},\n\n"
        f"Confirm your account: {confirmation_url}\n\n"
        "The link is valid for 3 days. If you did not sign up, ignore this e-mail.",
        None,
        [user.email],
        fail_silently=True,
    )
    return confirmation_url
