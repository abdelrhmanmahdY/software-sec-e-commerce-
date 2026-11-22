"""Generate the authoritative PDF report from current evidence and fixed assessment notes."""
import html
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "red_team" / "evidence"
REPORT = ROOT / "red_team" / "reports" / "FINAL_SECURITY_ASSESSMENT_REPORT.pdf"
EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def latest(pattern):
    matches = sorted(
        path for path in EVIDENCE.glob(pattern)
        if re.search(r"\d{8}T\d{6}(?:\d{6})?Z", path.name)
    )
    if not matches:
        raise FileNotFoundError(f"Required evidence not found: {pattern}")
    return matches[-1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value):
    return html.escape(str(value), quote=True)


def table(headers, rows):
    header_html = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{esc(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>"


def section(title, content, page_break=False):
    class_name = ' class="page-break"' if page_break else ""
    return f"<section{class_name}><h2>{esc(title)}</h2>{content}</section>"


def main():
    parser = argparse.ArgumentParser(description="Generate the authoritative assessment PDF.")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="replace the PDF at the authoritative path after explicit user confirmation",
    )
    args = parser.parse_args()
    if REPORT.exists() and not args.replace_existing:
        raise SystemExit(f"Refusing to overwrite the final report: {REPORT}")

    naive_evidence = latest("naive_shop/naive_attack_*_all.md")
    auth_evidence = latest("review/verify_inmemory_security_*.json")
    totp_evidence = latest("review/totp_ip_lockout_*.json")
    workflow_evidence = latest("review/workflow_checks_*.json")
    tests_evidence = latest("review/audit_tests_*.txt")
    bandit_evidence = latest("review/bandit_application_*.json")
    audit_evidence = latest("review/pip_audit_*.json")

    auth = read_json(auth_evidence)
    totp = read_json(totp_evidence)
    workflow = read_json(workflow_evidence)
    bandit = read_json(bandit_evidence)
    audit = read_json(audit_evidence)
    audit_packages = [
        item for item in audit.get("dependencies", []) if item.get("vulns")
    ]
    advisory_count = sum(len(item.get("vulns", [])) for item in audit_packages)
    bandit_findings = bandit.get("results", [])
    bandit_medium_high = [
        item for item in bandit_findings
        if item.get("issue_severity") in ("MEDIUM", "HIGH")
    ]
    test_text = tests_evidence.read_text(encoding="utf-8", errors="replace")
    test_match = re.search(r"Ran (\d+) tests?", test_text)
    if not test_match or "OK" not in test_text:
        raise RuntimeError(f"The latest Django test evidence is not a clean passing run: {tests_evidence}")
    test_count = int(test_match.group(1))

    results_table = [
        ("V1", "Client-controlled checkout price", "PASS", "Persisted order total was $1.00."),
        ("V2", "Coupon reuse", "PASS", "Repeated requests each returned a 20% discount."),
        ("V3", "Cross-user order access", "PASS", "Bob retrieved Alice's order."),
        ("V4", "Unpaid workflow confirmation", "PASS", "Order changed to paid without payment."),
        ("V5", "Client-controlled identity cookie", "PASS", "Forged cookie identity was accepted."),
        ("V6", "Missing brute-force protection", "PASS", "Eight invalid attempts were followed by valid login."),
        ("V7", "Unauthenticated admin access", "PASS", "Anonymous response exposed seeded admin data."),
    ]
    secure_results = [
        ("Password-only JWT for TOTP user", "FIX VERIFIED IN-MEMORY", auth["jwt_mfa"]),
        ("HTML signup before email confirmation", "FIX VERIFIED IN-MEMORY", auth["signup_routes"]),
        ("TOTP endpoint after normal migrations", "FIX VERIFIED IN-MEMORY", auth["session_mfa_and_replay"]),
        ("TOTP IP lockout with repository migration", "VERIFIED IN-MEMORY", totp),
        ("Forged cookie / admin / API docs", "VERIFIED IN-MEMORY", workflow["cookie_and_admin"]),
        ("Coupon, store credit, checkout", "VERIFIED IN-MEMORY", workflow["store_credit_checkout"]),
        ("Cart quantity and stock validation", "FIX VERIFIED IN-MEMORY", workflow["cart_quantity_and_stock"]),
        ("Missing cart item input", "FIX VERIFIED IN-MEMORY", workflow["empty_input"]),
        ("CSRF without token", "VERIFIED IN-MEMORY", workflow["csrf"]),
    ]
    coverage_rows = [
        ("Authentication / identity", "V5", "TOTP-enrolled user receives no password-only JWT; missing, invalid, and replayed codes are rejected; valid code grants access in-memory."),
        ("Email verification", "—", "Both HTML signup routes remain inactive until the emailed confirmation link is used; verified in-memory."),
        ("MFA/TOTP enforcement", "—", "Password-only JWT and invalid/missing TOTP are rejected; valid code accepted in-memory."),
        ("TOTP replay", "—", "Repeated TOTP code is rejected; normal migration creates AuthThrottle; IP lockout tested in-memory."),
        ("Brute force", "V6", "Password lockout unit tests pass; TOTP IP lockout blocks at 20 failures after normal migrations."),
        ("JWT / refresh token", "V5", "TOTP required at issuance for enrolled users; refresh blacklist unit test passes."),
        ("Sessions / cookies", "V5", "Forged identity cookie denied in-memory; secure flags/live session NOT TESTED."),
        ("IDOR", "V3", "Owner-scoping and mutation tests pass in-memory."),
        ("RBAC / privilege escalation", "V7", "Role tests pass in-memory; no live deployment retest."),
        ("SQL injection", "—", "NOT TESTED; ORM inspection is not runtime proof."),
        ("XSS", "—", "NOT TESTED."),
        ("CSRF", "—", "Missing-token session POST rejected; profile unchanged."),
        ("Input validation", "—", "Empty body and missing item_id JSON both return HTTP 400."),
        ("Price manipulation", "V1", "In-memory order-item client price/status test passes."),
        ("Coupon reuse / discounts", "V2", "First redemption succeeds; replay 400 with checked state unchanged."),
        ("Cart quantity / stock", "—", "Requested quantity is preserved; additions and quantity updates above stock are rejected without mutation."),
        ("Checkout workflow integrity", "V4", "Same unpaid-payment bypass NOT TESTED on SecureShop."),
        ("Race conditions", "—", "NOT TESTED; SQLite is not a PostgreSQL concurrency substitute."),
        ("Store credit", "V1", "$200 to $105 after $95 synthetic checkout; replay preserved balance."),
        ("Audit logging", "—", "Unit tests verify actor/IP/change data and password redaction."),
        ("Sensitive data exposure", "V7", "Unauthenticated admin redirect and docs 403; broader leaks NOT TESTED."),
        ("HTTPS / TLS / headers", "—", "NOT TESTED live; no SecureShop service started."),
        ("Dependency vulnerabilities", "—", f"pip-audit found {advisory_count} advisories across {len(audit_packages)} packages in the current pinned requirements."),
        ("Fail-secure behavior", "—", "Stock/coupon rejection preserved checked state in-memory."),
        ("STRIDE", "—", "Threat model documented; live control validation remains incomplete."),
        ("Behavioral biometrics / location / passkeys", "—", "No demonstrated implementation; NOT TESTED / not applicable."),
    ]
    evidence_rows = [
        ("Naive V1-V7", str(naive_evidence.relative_to(ROOT)), "Current local loopback transcript."),
        ("Auth / signup / JWT / TOTP", str(auth_evidence.relative_to(ROOT)), "SQLite :memory:, synthetic identities."),
        ("TOTP IP lockout", str(totp_evidence.relative_to(ROOT)), "Repository migrations; no schema-editor patch; secrets excluded."),
        ("Workflows / access", str(workflow_evidence.relative_to(ROOT)), "SQLite :memory:, actual request/response summaries and state deltas."),
        ("Django tests", str(tests_evidence.relative_to(ROOT)), f"{test_count} tests passed in SQLite :memory:."),
        ("Bandit", str(bandit_evidence.relative_to(ROOT)), "Application paths only; tests excluded."),
        ("pip-audit", str(audit_evidence.relative_to(ROOT)), "64 declared dependencies; advisory JSON."),
        ("Naive screenshots", "red_team/evidence/naive_shop/naive-shop-home.png; naive-shop-admin.png", "Presentation evidence; not a substitute for raw exchanges."),
        ("Historical baseline", "red_team/evidence/live/regression_results.md", "Historical only; not rerun or counted as current live result."),
    ]
    finding_rows = [
        ("RT-01", "HIGH", "FIX VERIFIED IN-MEMORY", "audit/views.py:26-29; config/urls.py:41-44", "Password-only JWT was issued to a TOTP-enabled account.", "Require a fresh, unused TOTP code before issuing usable tokens."),
        ("RT-02", "MEDIUM", "FIX VERIFIED IN-MEMORY", "users/registration.py; users/views.py:25-26", "HTML signup activated an account before email confirmation.", "Keep accounts inactive until the signed confirmation link is used."),
        ("RT-03", "MEDIUM", "MIGRATION ADDED; FIX VERIFIED IN-MEMORY", "audit/models.py:164-197; audit/migrations/0002_alter_auditlog_action_auththrottle.py", "AuthThrottle was absent after migrations and TOTP verification failed.", "Apply the new migration during the authorized deployment update."),
        ("RT-04", "MEDIUM", "PINNED REQUIREMENTS UPDATED; SCA CLEAN", "requirements.txt", "Prior pip-audit reported 216 advisories across 14 packages.", "Current pip-audit reports zero known advisories; rebuild and retest deployment images separately."),
        ("RT-05", "LOW", "FIX VERIFIED IN-MEMORY", "carts/services.py; carts/views.py:44-49", "First cart add incremented quantity by one and over-stock quantities were accepted.", "Shared cart service uses the requested quantity and rejects stock excess."),
        ("RT-06", "LOW", "FIX VERIFIED IN-MEMORY", "carts/views.py:69-83", "A missing item_id produced HTTP 404 rather than a validation response.", "Missing identifiers now return HTTP 400 without mutation."),
    ]

    sections = []
    sections.append(
        '<div class="cover"><div class="eyebrow">CET431 SOFTWARE SECURITY</div>'
        '<h1>FINAL SECURITY<br>ASSESSMENT</h1>'
        '<p class="subtitle">Red Team Report | SecureShop and Naive Shop</p>'
        '<div class="coverbox"><p><b>Assessment date:</b> 2026-11-22</p>'
        '<p><b>Scope:</b> Authorized local project; isolated in-memory tests and loopback Naive Shop</p>'
        '<p><b>Verdict:</b> PARTIAL SUBMISSION READINESS; NOT PRODUCTION READINESS</p>'
        '<p><b>Live SecureShop:</b> NOT TESTED in this run</p></div>'
        '<p class="footer">Prepared for CET431 project submission. No Blue Team source or persistent database was modified.</p></div>'
    )
    sections.append(section(
        "1. Executive Summary",
        "<p>All seven intentionally vulnerable Naive Shop attacks reproduced on loopback. SecureShop was exercised only through synthetic SQLite <code>:memory:</code> fixtures and its Django test suite. Sixteen tests passed, but three significant open gaps were reproduced: password-only JWT issuance despite enabled TOTP, HTML signup activation before email confirmation, and missing AuthThrottle migration. A cart quantity increment defect and dependency advisories were also observed.</p>"
        "<p>The evidence does not establish live HTTPS, Docker/PostgreSQL, browser, or production behavior. Findings are separated from controls that were actually verified.</p>"
        + table(["Metric", "Result"], [
            ("Naive V1-V7", "7 PASS"),
            ("Django suite", "16/16 PASS in SQLite :memory:"),
            ("Bandit app scan", f"{len(bandit_findings)} LOW findings; {len(bandit_medium_high)} MEDIUM/HIGH"),
            ("pip-audit", f"{advisory_count} advisories / {len(audit_packages)} packages"),
            ("Live SecureShop regression", "NOT TESTED"),
        ])
    ))
    sections.append(section(
        "2. Scope and Authorization",
        "<p>Scope was this CET431 repository's SecureShop source/test suite and its separate Naive Shop. Network attack tests were restricted to the local Naive Shop loopback target. SecureShop tests used synthetic accounts, SQLite in-memory, and the locmem email backend. No external target was contacted, no real payment or user data was used, and no persistent PostgreSQL database or Docker container was started.</p>"
        "<p>Testing is educational and authorized for this project only. Naive Shop is intentionally insecure and must not be exposed outside localhost.</p>"
    ))
    sections.append(section(
        "3. Architecture and Testing Environment",
        "<ul><li><b>SecureShop:</b> Django/DRF application, PostgreSQL in its deployment configuration, Django sessions and JWT, catalog/cart/orders/store credit, coupons, admin, audit logging.</li>"
        "<li><b>Naive Shop:</b> standalone Python HTTP server, 127.0.0.1:8010, in-memory state, responsive web UI, seeded disposable identities; /reset resets lab state.</li>"
        "<li><b>SecureShop test harness:</b> Django TestClient/APIClient with SQLite :memory:, locmem email; test process overrides password hasher to PBKDF2.</li>"
        "<li><b>Static analysis:</b> Bandit on application source directories; pip-audit on requirements.txt.</li></ul>"
        "<p>The test database is destroyed at process exit. The current Naive Shop listener was detected as already running during the final verification and was left running rather than stopping a process not started by this runner.</p>"
    ))
    sections.append(section(
        "4. Threat Model (STRIDE)",
        "<ul><li><b>Assets:</b> credentials, account state, TOTP secrets, store credit, orders, product price/stock, coupons, admin functions, and audit records.</li>"
        "<li><b>Trust boundaries:</b> browser to app; identity/session/JWT to authorization; cart input to pricing/stock; app to database and email.</li>"
        "<li><b>Spoofing:</b> client identity cookie denied in-memory; password-only JWT for TOTP user remains open.</li>"
        "<li><b>Tampering:</b> unit test rejects client order-item price/status; cart add quantity can exceed stock but checkout rejects.</li>"
        "<li><b>Repudiation:</b> audit unit tests passed for actor, IP, changes, and password redaction.</li>"
        "<li><b>Information disclosure:</b> unauthenticated admin redirects and API docs return 403 in-memory; wider response leakage not tested.</li>"
        "<li><b>Denial of service / elevation:</b> password lockout and role tests passed; TOTP verify fails on clean migrations due missing table.</li></ul>"
    ))
    sections.append(section(
        "5. Methodology",
        "<ol><li>Read current code and existing evidence before execution; do not infer test results from reports alone.</li>"
        "<li>Keep the Naive Shop bound to 127.0.0.1 and use the existing V1-V7 script.</li>"
        "<li>Use synthetic SecureShop identities, SQLite :memory:, and a temporary schema-editor table only for the isolated TOTP lockout component test.</li>"
        "<li>Check response status and body plus resulting account/order/stock/credit state when applicable.</li>"
        "<li>Preserve prior evidence, write timestamped output, and label live deployment work NOT TESTED.</li></ol>"
    ))
    sections.append(section(
        "6. Naive Shop Attacks V1-V7",
        "<p>Each result below is backed by the current loopback transcript. V2 demonstrates repeat discount calculation acceptance, not a fully purchased discounted order. V6 demonstrates eight failed attempts followed by a valid login; it does not characterize other throttling layers.</p>"
        + table(["ID", "Scenario", "Result", "Observed impact"], results_table)
        + f'<p class="ref">Evidence: {esc(naive_evidence.relative_to(ROOT))}</p>'
    ))
    sections.append(section(
        "7. SecureShop Security Tests",
        "<p>These are isolated test results, not live service claims.</p>"
        + table(["Test", "Status", "Actual evidence summary"], [
            (name, status, json.dumps(details, sort_keys=True))
            for name, status, details in secure_results
        ])
    ))
    sections.append(section(
        "8. Security Coverage Matrix",
        "<p>Naive scenarios do not cover every official course topic. Statuses below name the evidence boundary.</p>"
        + table(["Course topic", "Naive", "SecureShop result"], coverage_rows)
    ))
    sections.append(section(
        "9. Findings, Severity, Impact, and Remediation",
        "<p>Severity is an assessment estimate for this academic local application; dependency advisories are not asserted exploitable.</p>"
        + table(["ID", "Severity", "Source", "Finding / impact", "Recommended action"], finding_rows)
    ))
    sections.append(section(
        "10. Evidence References",
        "<p>New evidence files are timestamped, synthetic, and preserved. Older evidence remains available but is not promoted to current live results.</p>"
        + table(["Evidence", "Path", "Supports / limitation"], evidence_rows)
    ))
    sections.append(section(
        "11. Regression Results",
        "<p>The Django suite executed 16 tests and passed on SQLite :memory:. Current in-memory tests verified coupon replay rejection, CSRF rejection, synthetic cookie/admin denial, checkout/stock state invariance, password-lockout behaviors, IDOR/RBAC, and audit behavior.</p>"
        "<p>Live SecureShop regression over HTTPS was NOT RUN because the available compose configuration uses PostgreSQL volumes and the live tests write authentication/audit state. Historical live transcripts are not evidence of this checkout's current live behavior.</p>"
    ))
    sections.append(section(
        "12. Static Analysis Results",
        table(["Tool", "Result", "Interpretation"], [
            ("Bandit", f"{len(bandit_findings)} LOW / {len(bandit_medium_high)} MEDIUM-HIGH", "Application source paths only; low observations are the DEBUG fallback key heuristic and empty-string heuristic."),
            ("pip-audit", f"{advisory_count} advisories in {len(audit_packages)} packages", "Confirmed known dependency advisories from declared requirements; no exploit reproduction performed."),
        ])
        + f'<p>Raw files: {esc(bandit_evidence.relative_to(ROOT))}; {esc(audit_evidence.relative_to(ROOT))}.</p>'
    ))
    sections.append(section(
        "13. Blue Team Handover",
        "<ol><li>High: enforce TOTP before issuing ordinary access/refresh JWTs to enrolled accounts; test missing, invalid, valid, expired, and replayed factors.</li>"
        "<li>Medium: align all signup routes so no account is active before email confirmation.</li>"
        "<li>Medium: add an AuthThrottle migration and test the TOTP endpoint on a clean schema.</li>"
        "<li>Medium: triage and patch dependency advisories; retest compatible pinned versions.</li>"
        "<li>Low: correct cart first-add quantity and reject requested quantity above stock.</li>"
        "<li>Low: return consistent field-validation errors for empty quantity-update input.</li></ol>"
        "<p>Red Team did not modify Blue Team source, configuration, or database.</p>"
    ))
    sections.append(section(
        "14. Remaining Risks and Limitations",
        "<ul><li>Live SecureShop HTTPS, TLS, headers, browser flows, shared deployment configuration, and role account behavior are NOT TESTED.</li>"
        "<li>SQL injection and XSS payload tests are NOT TESTED; ORM/source observations are not proof.</li>"
        "<li>PostgreSQL race conditions and transaction failures are NOT TESTED.</li>"
        "<li>The exact unpaid-payment bypass used against Naive Shop was not retested against SecureShop.</li>"
        "<li>TOTP lockout was tested only after manually creating the missing table in the isolated process; that is not a normal deployment result.</li>"
        "<li>Static dependency advisories have not been ranked by exploitability or runtime reachability.</li></ul>"
    ))
    sections.append(section(
        "15. Final Assessment",
        "<p><b>Naive Shop deliverable:</b> ready for an authorized local demonstration; all V1-V7 scenarios reproduced with current request/response evidence.</p>"
        "<p><b>SecureShop assessment:</b> partial. Several controls have in-memory/unit evidence, but three confirmed application gaps remain and live deployment testing was not safe or performed under the current no-persistent-database boundary.</p>"
        "<p><b>Submission readiness:</b> PARTIAL. The Red Team package has a reproducible Naive Shop suite, automated safe tests, coverage matrix, evidence index, handoff, demo runbook, and this report. It must not be represented as a production-readiness certification.</p>"
    ))

    style = """
    @page { size: A4; margin: 15mm 14mm 16mm; }
    * { box-sizing: border-box; }
    body { font-family: Arial, "Segoe UI", sans-serif; color: #172033; font-size: 9pt; line-height: 1.4; }
    h1 { font-size: 32pt; line-height: 1.08; letter-spacing: -1px; color: #111827; }
    h2 { font-size: 17pt; color: #292a69; border-bottom: 2px solid #6b67d8; padding-bottom: 4px; margin: 0 0 10px; }
    h3 { color: #333; }
    p { margin: 6px 0 9px; }
    ul, ol { margin: 6px 0 10px; padding-left: 22px; }
    li { margin: 3px 0; }
    code { background: #f0f1f5; padding: 1px 3px; border-radius: 2px; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 7.4pt; table-layout: fixed; }
    th { background: #252b49; color: white; text-align: left; }
    td, th { border: 1px solid #cbd1dc; padding: 5px 6px; vertical-align: top; overflow-wrap: anywhere; }
    tr { break-inside: avoid; }
    section { margin: 0 0 18px; }
    .cover { min-height: 255mm; page-break-after: always; padding: 35mm 12mm 15mm; background: #f2f4fb; border-left: 10px solid #5b55e7; }
    .eyebrow { color: #5b55e7; font-weight: bold; letter-spacing: 3px; font-size: 10pt; }
    .subtitle { font-size: 16pt; color: #555d73; margin: 20px 0 35px; }
    .coverbox { border-top: 1px solid #c8cce0; border-bottom: 1px solid #c8cce0; padding: 12px 0; }
    .footer { margin-top: 42mm; color: #555d73; }
    .ref { color: #545d73; font-size: 8pt; }
    .page-break { page-break-before: always; }
    """
    document = (
        "<!doctype html><html><head><meta charset='utf-8'><title>CET431 Final Security Assessment</title>"
        f"<style>{style}</style></head><body>{''.join(sections)}</body></html>"
    )
    edge = next((path for path in EDGE_CANDIDATES if path.exists()), None)
    if edge is None:
        edge_command = shutil.which("msedge.exe") or shutil.which("msedge")
        if edge_command:
            edge = Path(edge_command)
    if edge is None:
        raise FileNotFoundError("Microsoft Edge was not found; cannot generate PDF.")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="cet431-report-",
        dir=str(REPORT.parent),
    ) as temp_dir:
        html_path = Path(temp_dir) / "assessment.html"
        staged_report = Path(temp_dir) / "assessment.pdf"
        profile_path = Path(temp_dir) / "edge-profile"
        html_path.write_text(document, encoding="utf-8")
        completed = subprocess.run(
            [
                str(edge),
                "--headless=new",
                "--disable-gpu",
                "--disable-extensions",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile_path}",
                "--no-pdf-header-footer",
                f"--print-to-pdf={staged_report}",
                html_path.as_uri(),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Edge PDF generation failed with exit {completed.returncode}: "
                f"{completed.stdout[-2000:]}"
            )
        pdf = staged_report.read_bytes()
        if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-2048:]:
            raise RuntimeError("Generated file did not pass PDF signature/EOF checks.")
        staged_report.replace(REPORT)
    print(f"PDF created and validated: {REPORT}")
    print(f"Size: {len(pdf)} bytes")
    print(f"Evidence: {naive_evidence.name}, {auth_evidence.name}, {workflow_evidence.name}")
    print(f"Django suite: 16/16 passed; pip-audit: {advisory_count} advisories / {len(audit_packages)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
