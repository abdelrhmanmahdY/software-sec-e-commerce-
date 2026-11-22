"""Run Bandit and pip-audit into new, timestamped evidence files."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "red_team" / "evidence" / "review"


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    bandit_path = EVIDENCE / f"bandit_application_{stamp}.json"
    audit_path = EVIDENCE / f"pip_audit_{stamp}.json"
    if bandit_path.exists() or audit_path.exists():
        raise SystemExit("Refusing to overwrite timestamped static-analysis evidence.")
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    bandit = subprocess.run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "audit",
            "config",
            "dashboard",
            "orders",
            "products",
            "users",
            "carts",
            "-x",
            "*/tests.py",
            "-f",
            "json",
            "-o",
            str(bandit_path),
            "--exit-zero",
        ],
        cwd=str(ROOT),
        check=False,
    )
    if bandit.returncode != 0 or not bandit_path.exists():
        print(f"Bandit: INCONCLUSIVE (exit {bandit.returncode})")
        return 2
    bandit_result = json.loads(bandit_path.read_text(encoding="utf-8"))
    findings = bandit_result.get("results", [])
    med_high = [
        item for item in findings
        if item.get("issue_severity") in ("MEDIUM", "HIGH")
    ]
    print(
        f"Bandit: {'FAIL' if med_high else 'PASS'} "
        f"({len(findings)} findings; {len(med_high)} medium/high)"
    )
    print(f"Bandit evidence: {bandit_path}")

    audit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            "requirements.txt",
            "--format",
            "json",
            "--output",
            str(audit_path),
        ],
        cwd=str(ROOT),
        check=False,
    )
    if not audit_path.exists():
        print(f"pip-audit: INCONCLUSIVE (exit {audit.returncode}; no JSON output)")
        return 2
    audit_result = json.loads(audit_path.read_text(encoding="utf-8"))
    vulnerable = [
        dependency
        for dependency in audit_result.get("dependencies", [])
        if dependency.get("vulns")
    ]
    advisory_count = sum(len(item.get("vulns", [])) for item in vulnerable)
    if audit.returncode not in (0, 1):
        print(f"pip-audit: INCONCLUSIVE (exit {audit.returncode})")
        return 2
    print(
        f"pip-audit: {'FAIL' if advisory_count else 'PASS'} "
        f"({advisory_count} advisories across {len(vulnerable)} packages)"
    )
    print(f"pip-audit evidence: {audit_path}")

    return 1 if med_high or advisory_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
