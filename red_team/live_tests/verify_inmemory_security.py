"""Verify selected SecureShop auth controls without touching shared data.

This script forces an in-memory SQLite database and an in-memory email backend.
It never contacts the running Docker/PostgreSQL deployment. PBKDF2 is selected
only inside this test process because the configured bcrypt package is absent.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone


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

from users.totp import get_totp_code


settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
logging.disable(logging.CRITICAL)
call_command("migrate", interactive=False, verbosity=0)

PASSWORD = "Disposable-Only-Current-Head-Test-2026!"


def new_user(username):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.test",
        password=PASSWORD,
    )
    return user


def run():
    # All account rows and mail messages below live only in SQLite :memory:.
    form_data = {
        "first_name": "Disposable",
        "last_name": "User",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    client = Client()
    html_response = client.post(
        "/signup/",
        {**form_data, "username": "rt_html", "email": "rt_html@example.test"},
    )
    html_user = User.objects.get(username="rt_html")
    dashboard_response = client.post(
        "/dashboard/signup/",
        {**form_data, "username": "rt_dashboard", "email": "rt_dashboard@example.test"},
    )
    dashboard_user = User.objects.get(username="rt_dashboard")
    api_response = client.post(
        "/api/users/signup/",
        data=json.dumps({
            "username": "rt_api",
            "email": "rt_api@example.test",
            "password": PASSWORD,
        }),
        content_type="application/json",
    )
    api_user = User.objects.get(username="rt_api")
    signup = {
        "html_status": html_response.status_code,
        "html_active": html_user.is_active,
        "html_email_confirmed": html_user.profile.email_confirmed,
        "dashboard_status": dashboard_response.status_code,
        "dashboard_active": dashboard_user.is_active,
        "api_status": api_response.status_code,
        "api_active": api_user.is_active,
    }
    assert not signup["html_active"] and not signup["html_email_confirmed"]
    assert not signup["dashboard_active"] and not signup["api_active"]

    # Password-only JWT issuance for an account whose TOTP flag is enabled.
    mfa_user = new_user("rt_mfa")
    mfa_user.profile.totp_enabled = True
    mfa_user.profile.totp_secret = "TESTONLYBASE32SECRET"
    mfa_user.profile.save(update_fields=["totp_enabled", "totp_secret"])
    mfa_client = Client()
    valid_totp_code = get_totp_code(mfa_user.profile.totp_secret)
    invalid_totp_code = (
        "000000" if valid_totp_code != "000000" else "000001"
    )
    password_only_response = mfa_client.post(
        "/api/auth/login/",
        data=json.dumps({"username": mfa_user.username, "password": PASSWORD}),
        content_type="application/json",
    )
    invalid_code_response = mfa_client.post(
        "/api/auth/login/",
        data=json.dumps({
            "username": mfa_user.username,
            "password": PASSWORD,
            "totp_code": invalid_totp_code,
        }),
        content_type="application/json",
    )
    totp_code = valid_totp_code
    jwt_response = mfa_client.post(
        "/api/auth/login/",
        data=json.dumps({
            "username": mfa_user.username,
            "password": PASSWORD,
            "totp_code": totp_code,
        }),
        content_type="application/json",
    )
    access = jwt_response.json().get("access")
    protected_response = (
        mfa_client.get(
            "/api/orders/orders/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        if access else None
    )
    replay_response = mfa_client.post(
        "/api/auth/login/",
        data=json.dumps({
            "username": mfa_user.username,
            "password": PASSWORD,
            "totp_code": totp_code,
        }),
        content_type="application/json",
    )
    jwt_mfa = {
        "totp_enabled": mfa_user.profile.totp_enabled,
        "totp_submitted": True,
        "password_only_status": password_only_response.status_code,
        "password_only_access_issued": bool(password_only_response.json().get("access")),
        "invalid_totp_status": invalid_code_response.status_code,
        "valid_totp_status": jwt_response.status_code,
        "access_issued": bool(access),
        "protected_orders_status": protected_response.status_code if protected_response else None,
        "same_code_replay_status": replay_response.status_code,
    }
    assert jwt_mfa["password_only_status"] == 401
    assert not jwt_mfa["password_only_access_issued"]
    assert jwt_mfa["invalid_totp_status"] == 401
    assert jwt_mfa["valid_totp_status"] == 200 and jwt_mfa["access_issued"]
    assert jwt_mfa["protected_orders_status"] == 200
    assert jwt_mfa["same_code_replay_status"] == 401

    # TOTP verification cannot reach its policy logic if the throttle table is absent.
    session_user = new_user("rt_session_mfa")
    session_profile = session_user.profile
    session_profile.totp_enabled = True
    session_profile.totp_secret = "TESTONLYSESSIONSECRET"
    session_profile.save(update_fields=["totp_enabled", "totp_secret"])
    session_client = Client()
    login_response = session_client.post(
        reverse("login"),
        {"username": session_user.username, "password": PASSWORD},
    )
    before_factor = "_auth_user_id" not in session_client.session
    code = get_totp_code(session_profile.totp_secret)
    auththrottle_table_exists = "audit_auththrottle" in connection.introspection.table_names()
    verify_response = session_client.post(reverse("totp_verify"), {"code": code})
    session_profile.refresh_from_db()
    session_authenticated_after_totp = "_auth_user_id" in session_client.session
    session = {
        "password_login_status": login_response.status_code,
        "unauthenticated_before_totp": before_factor,
        "auththrottle_table_exists_after_migrations": auththrottle_table_exists,
        "totp_verify_status": verify_response.status_code,
        "authenticated_after_totp": session_authenticated_after_totp,
        "last_totp_counter_recorded": session_profile.last_totp_counter is not None,
    }
    assert before_factor and auththrottle_table_exists
    assert verify_response.status_code == 302 and session_authenticated_after_totp
    assert session["last_totp_counter_recorded"]

    # TOTP setup and disablement are exercised only on a temporary account.
    setup_user = new_user("rt_setup")
    setup_client = Client()
    setup_client.force_login(setup_user)
    setup_url = reverse("totp_setup")
    get_setup = setup_client.get(setup_url)
    setup_user.profile.refresh_from_db()
    setup_code = get_totp_code(setup_user.profile.totp_secret)
    enable_response = setup_client.post(setup_url, {"code": setup_code})
    setup_user.profile.refresh_from_db()
    enabled = setup_user.profile.totp_enabled
    disable_response = setup_client.post(setup_url, {"action": "disable"})
    setup_user.profile.refresh_from_db()
    setup = {
        "get_status": get_setup.status_code,
        "enable_status": enable_response.status_code,
        "enabled_after_valid_code": enabled,
        "disable_status": disable_response.status_code,
        "disabled_after_action": not setup_user.profile.totp_enabled,
        "secret_cleared_after_disable": not setup_user.profile.totp_secret,
        "counter_cleared_after_disable": setup_user.profile.last_totp_counter is None,
    }
    assert setup["enabled_after_valid_code"]
    assert setup["disabled_after_action"] and setup["secret_cleared_after_disable"]
    assert setup["counter_cleared_after_disable"]

    return {
        "database": "SQLite :memory:",
        "email_backend": "locmem",
        "password_hasher_override": "PBKDF2 (test process only)",
        "signup_routes": signup,
        "jwt_mfa": jwt_mfa,
        "session_mfa_and_replay": session,
        "totp_setup_disable": setup,
        "totp_lockout_route_tested": True,
        "totp_lockout_blocker": None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify selected SecureShop auth controls with temporary SQLite only."
    )
    evidence_dir = ROOT / "red_team" / "evidence" / "review"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser.add_argument(
        "--output",
        type=Path,
        default=evidence_dir / f"verify_inmemory_security_{timestamp}.json",
        help="new evidence JSON path inside red_team/evidence/review/",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != evidence_dir.resolve():
        parser.error("output must stay inside red_team/evidence/review/")
    if output.exists():
        parser.error(f"refusing to overwrite existing evidence: {output}")
    result = run()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"Evidence: {output}")
