"""Run only disposable in-memory tests and the local loopback Naive Shop suite."""
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS = [
    ("Registration and MFA", "verify_inmemory_security.py"),
    ("TOTP IP lockout", "verify_inmemory_totp_ip_lockout.py"),
    ("Workflows and access", "verify_inmemory_workflows.py"),
    ("Django in-memory tests", "run_isolated_audit_tests.py"),
    ("Naive Shop V1-V7", "run_naive_suite.py"),
]


def main():
    results = []
    for label, script in RUNS:
        path = ROOT / "red_team" / "live_tests" / script
        print(f"\n=== {label} ===", flush=True)
        completed = subprocess.run([sys.executable, str(path)], cwd=str(ROOT), check=False)
        if completed.returncode == 0:
            status = "PASS"
        elif completed.returncode == 2:
            status = "INCONCLUSIVE"
        else:
            status = "FAIL"
        results.append((label, status, completed.returncode))

    print("\nSafe-suite summary")
    for label, status, code in results:
        print(f"{status:12} {label} (exit {code})")
    if any(status == "FAIL" for _, status, _ in results):
        return 1
    if any(status == "INCONCLUSIVE" for _, status, _ in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
