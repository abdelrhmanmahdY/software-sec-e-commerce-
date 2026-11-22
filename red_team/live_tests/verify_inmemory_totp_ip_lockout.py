"""Verify TOTP IP lockout with synthetic users and ephemeral SQLite only."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEBUG"] = "True"
os.environ["EMAIL_BACKEND"] = "django.core.mail.backends.locmem.EmailBackend"
os.environ["SECRET_KEY"] = "CET431-RedTeam-InMemory-Test-Key-Only-2026"

import django

django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.urls import reverse

from audit.models import AuthThrottle
from audit.utils import is_totp_locked_out
from users.totp import get_totp_code, verify_totp_code


settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
settings.TRUST_PROXY_HEADERS = False
logging.disable(logging.CRITICAL)

LOCKOUT_IP = "192.0.2.7"
OTHER_IP = "192.0.2.8"


def invalid_code(secret):
    for candidate in range(1_000_000):
        code = f"{candidate:06d}"
        if not verify_totp_code(secret, code):
            return code
    raise AssertionError("Could not find an invalid TOTP code.")


def preauth_client(user, remote_addr):
    client = Client(REMOTE_ADDR=remote_addr)
    session = client.session
    session["pre_2fa_user_id"] = user.pk
    session["pre_2fa_backend"] = "django.contrib.auth.backends.ModelBackend"
    session.save()
    return client


def main():
    parser = argparse.ArgumentParser(
        description="Test TOTP IP lockout without touching persistent databases."
    )
    evidence_dir = ROOT / "red_team" / "evidence" / "review"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser.add_argument(
        "--output",
        type=Path,
        default=evidence_dir / f"totp_ip_lockout_{timestamp}.json",
        help="new evidence JSON path inside red_team/evidence/review/",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != evidence_dir.resolve():
        parser.error("output must stay inside red_team/evidence/review/")
    if output.exists():
        parser.error(f"refusing to overwrite existing evidence: {output}")

    call_command("migrate", interactive=False, verbosity=0)
    table_exists_after_migrations = (
        AuthThrottle._meta.db_table in connection.introspection.table_names()
    )
    if not table_exists_after_migrations:
        raise AssertionError(
            "AuthThrottle table is missing after the repository migrations."
        )

    users = []
    for index in range(6):
        user = User.objects.create_user(
            username=f"rt_totp_ip_{index}",
            email=f"rt_totp_ip_{index}@example.test",
        )
        user.profile.totp_enabled = True
        user.profile.totp_secret = "JBSWY3DPEHPK3PXP"
        user.profile.save(update_fields=["totp_enabled", "totp_secret"])
        users.append(user)

    route = reverse("totp_verify")
    failures = 0
    for user in users[:5]:
        client = preauth_client(user, LOCKOUT_IP)
        code = invalid_code(user.profile.totp_secret)
        for _ in range(4):
            response = client.post(route, {"code": code})
            if response.status_code != 200:
                raise AssertionError(f"Expected invalid code render HTTP 200; got {response.status_code}")
            failures += 1

    locked_after_threshold = is_totp_locked_out(users[5].pk, LOCKOUT_IP)
    locked_count_before = AuthThrottle.objects.filter(locked_until__isnull=False).count()
    locked_client = preauth_client(users[5], LOCKOUT_IP)
    locked_response = locked_client.post(
        route,
        {"code": invalid_code(users[5].profile.totp_secret)},
    )
    locked_response_text = locked_response.content.decode("utf-8", "replace")
    locked_count_after = AuthThrottle.objects.filter(locked_until__isnull=False).count()
    if not locked_after_threshold:
        raise AssertionError("TOTP IP was not locked after the configured threshold.")
    if "Too many verification attempts" not in locked_response_text:
        raise AssertionError("The endpoint did not display its locked response.")
    if locked_count_after != locked_count_before:
        raise AssertionError("The locked follow-up request changed lockout row count.")

    other_ip_client = preauth_client(users[5], OTHER_IP)
    valid_code = get_totp_code(users[5].profile.totp_secret)
    other_ip_response = other_ip_client.post(route, {"code": valid_code})
    authenticated_after_other_ip = "_auth_user_id" in other_ip_client.session
    if other_ip_response.status_code != 302 or not authenticated_after_other_ip:
        raise AssertionError("An unblocked IP could not complete the disposable user's TOTP login.")

    result = {
        "database": "SQLite :memory:",
        "endpoint": route,
        "auththrottle_table_exists_after_migrations": table_exists_after_migrations,
        "test_only_schema_editor_created_missing_table": False,
        "synthetic_users": len(users),
        "failed_codes_from_same_ip": failures,
        "ip_locked_at_threshold": locked_after_threshold,
        "locked_followup_http": locked_response.status_code,
        "locked_followup_did_not_add_lock_rows": locked_count_after == locked_count_before,
        "same_user_from_other_ip_http": other_ip_response.status_code,
        "other_ip_authenticated": authenticated_after_other_ip,
        "codes_and_secrets_recorded": False,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"Evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
