import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def generate_totp_secret(num_bytes: int = 20) -> str:
    """Generate a random Base32-encoded TOTP secret (RFC 6238)."""
    return base64.b32encode(secrets.token_bytes(num_bytes)).decode("ascii").rstrip("=")


def _normalize_b32(secret: str) -> bytes:
    cleaned = secret.strip().replace(" ", "").upper()
    pad = (-len(cleaned)) % 8
    return base64.b32decode(cleaned + ("=" * pad), casefold=True)


def get_totp_code(secret: str, for_time: int | None = None, step: int = 30, digits: int = 6) -> str:
    """Compute a 6-digit RFC 6238 TOTP code using HMAC-SHA1."""
    key = _normalize_b32(secret)
    counter = int((for_time if for_time is not None else time.time()) // step)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code_int).zfill(digits)


def verify_totp_code(secret: str, code: str, window: int = 1, step: int = 30) -> bool:
    """Verify a 6-digit TOTP code in constant time across +/- window steps."""
    if not secret or not code:
        return False
    cleaned = str(code).strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False
    now = int(time.time())
    for offset in range(-window, window + 1):
        expected = get_totp_code(secret, for_time=now + (offset * step), step=step)
        if hmac.compare_digest(expected, cleaned):
            return True
    return False


def get_otpauth_uri(username: str, secret: str, issuer: str = "SecureShop") -> str:
    label = quote(f"{issuer}:{username}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30"
