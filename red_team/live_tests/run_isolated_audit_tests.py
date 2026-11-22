"""Run the project's discovered Django tests with in-memory SQLite only."""
import io
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import traceback
from contextlib import redirect_stderr, redirect_stdout


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
from django.test.runner import DiscoverRunner


settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]


def main():
    evidence_dir = ROOT / "red_team" / "evidence" / "review"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = evidence_dir / f"audit_tests_{stamp}.txt"
    if output_path.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence: {output_path}")
    output = io.StringIO()
    result = 1
    try:
        with redirect_stdout(output), redirect_stderr(output):
            runner = DiscoverRunner(verbosity=2, interactive=False)
            failures = runner.run_tests([])
        result = 0 if failures == 0 else 1
    except Exception as error:
        output.write(f"\nTEST RUNNER ERROR: {type(error).__name__}: {error}\n")
        traceback.print_exc(file=output)
    report = output.getvalue()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report, end="" if report.endswith("\n") else "\n")
    print(f"Evidence: {output_path}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
