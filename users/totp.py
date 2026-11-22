
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from django.db import transaction


def generate_totp_secret(num_bytes: int = 20) -> str:
    """Generate a random Base32-encoded TOTP secret (RFC 6238)."""
    return base64.b32encode(
        secrets.token_bytes(num_bytes)
    ).decode("ascii").rstrip("=")


def _normalize_b32(secret: str) -> bytes:
    cleaned = secret.strip().replace(" ", "").upper()
    pad = (-len(cleaned)) % 8
    return base64.b32decode(
        cleaned + ("=" * pad),
        casefold=True
    )


def get_totp_code(
    secret: str,
    for_time: int | None = None,
    step: int = 30,
    digits: int = 6
) -> str:
    """Compute a 6-digit RFC 6238 TOTP code using HMAC-SHA1."""
    if step <= 0 or digits <= 0:
        raise ValueError("step and digits must be positive")

    key = _normalize_b32(secret)

    counter = int(
        (for_time if for_time is not None else time.time()) // step
    )

    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()

    offset = digest[-1] & 0x0F

    code_int = (
        struct.unpack(">I", digest[offset:offset + 4])[0]
        & 0x7FFFFFFF
    ) % (10 ** digits)

    return str(code_int).zfill(digits)


def verify_totp_code(
    secret: str,
    code: str,
    window: int = 1,
    step: int = 30
) -> bool:
    """Verify a 6-digit TOTP code without consuming it."""
    if not secret or not code or step <= 0:
        return False

    cleaned = str(code).strip().replace(" ", "")

    if not cleaned.isdigit() or len(cleaned) != 6:
        return False

    now = int(time.time())

    for offset in range(-window, window + 1):
        expected = get_totp_code(
            secret,
            for_time=now + (offset * step),
            step=step
        )

        if hmac.compare_digest(expected, cleaned):
            return True

    return False


def get_matching_totp_counter(
    secret: str,
    code: str,
    window: int = 1,
    step: int = 30
):
    """Return the matching TOTP counter."""
    if not secret or not code or step <= 0 or window < 0:
        return None

    cleaned = str(code).strip().replace(" ", "")

    if not cleaned.isdigit() or len(cleaned) != 6:
        return None

    current_counter = int(time.time() // step)

    for counter in range(
        current_counter + window,
        current_counter - window - 1,
        -1
    ):
        expected = get_totp_code(
            secret,
            for_time=counter * step,
            step=step
        )

        if hmac.compare_digest(expected, cleaned):
            return counter

    return None


def consume_totp_code(
    profile,
    code: str,
    window: int = 1,
    step: int = 30,
    require_enabled: bool = True
) -> bool:
    """
    Validate and atomically consume a TOTP counter.
    Prevents reuse of previously accepted TOTP codes.
    """

    with transaction.atomic():

        locked_profile = (
            profile.__class__.objects
            .select_for_update()
            .get(pk=profile.pk)
        )

        if require_enabled and not locked_profile.totp_enabled:
            return False

        if not locked_profile.totp_secret:
            return False

        counter = get_matching_totp_counter(
            locked_profile.totp_secret,
            code,
            window=window,
            step=step
        )

        if counter is None:
            return False

        last_counter = locked_profile.last_totp_counter

        if (
            last_counter is not None
            and counter <= last_counter
        ):
            return False

        locked_profile.last_totp_counter = counter

        locked_profile.save(
            update_fields=["last_totp_counter"]
        )

    profile.last_totp_counter = counter

    return True


def get_otpauth_uri(
    username: str,
    secret: str,
    issuer: str = "SecureShop"
) -> str:
    label = quote(f"{issuer}:{username}")

    return (
        f"otpauth://totp/{label}"
        f"?secret={secret}&issuer={quote(issuer)}"
        "&digits=6&period=30"
    )
