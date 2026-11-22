import binascii
import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.hashers import BCryptSHA256PasswordHasher
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import constant_time_compare


class PepperBCryptSHA256PasswordHasher(BCryptSHA256PasswordHasher):
    """bcrypt-SHA256 hasher with a server-side pepper supplied by PASSWORD_PEPPER."""

    algorithm = "bcrypt_sha256_pepper"

    def _peppered_password_bytes(self, password):
        pepper = getattr(settings, "PASSWORD_PEPPER", "")
        if not pepper:
            raise ImproperlyConfigured("PASSWORD_PEPPER must be configured.")
        peppered = hmac.new(
            pepper.encode("utf-8"),
            str(password).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return binascii.hexlify(hashlib.sha256(peppered.encode("utf-8")).digest())

    def salt(self):
        bcrypt = self._load_library()
        rounds = int(getattr(settings, "BCRYPT_ROUNDS", self.rounds))
        return bcrypt.gensalt(rounds)

    def encode(self, password, salt):
        bcrypt = self._load_library()
        data = bcrypt.hashpw(self._peppered_password_bytes(password), salt)
        return "%s$%s" % (self.algorithm, data.decode("ascii"))

    def verify(self, password, encoded):
        algorithm, data = encoded.split("$", 1)
        if algorithm != self.algorithm:
            return False
        bcrypt = self._load_library()
        encoded_2 = bcrypt.hashpw(
            self._peppered_password_bytes(password),
            data.encode("ascii"),
        ).decode("ascii")
        return constant_time_compare(data, encoded_2)
