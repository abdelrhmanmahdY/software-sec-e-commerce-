# 10–15 Minute Red Team Demo Runbook

## Readiness: PARTIAL — do not present live SecureShop defenses as freshly tested

The Naive Shop and SecureShop in-memory evidence are reproducible. Live SecureShop HTTPS/Docker/PostgreSQL behavior, mobile UI, TLS headers, and race conditions are **NOT TESTED** in this run.

## Exact sequence (about 12 minutes)

1. **0:00–1:00 — Scope and safety.** Open `red_team/README.md`. Explain that Naive Shop is intentionally vulnerable, loopback-only, and isolated; SecureShop live database was not started.
2. **1:00–2:00 — Architecture and threat model.** Open `reports/threat_model.md` and identify account, order, credit, and admin assets and trust boundaries.
3. **2:00–5:00 — Reproduce Naive attacks.** From repository root run:
   ```powershell
   python red_team/live_tests/run_naive_suite.py
   ```
   Expected: V1–V7 PASS; the script targets only `127.0.0.1:8010`, captures a new timestamped transcript, and will not stop a server it did not start.
4. **5:00–7:00 — Inspect evidence.** Open the latest `red_team/evidence/naive_shop/naive_attack_*_all.md`. Show V1 price, V3 IDOR, V4 unpaid confirmation, V5 cookie identity, and V7 anonymous admin request/response plus impact. Do not equate HTTP 200 alone with success.
5. **7:00–9:00 — SecureShop isolated findings.** Open the newest `workflow_checks_*.json` and `verify_inmemory_security_*.json`. Explain: cookie spoof denied; admin/docs access restricted; coupon replay blocked; over-stock checkout rejected without changing state; password-only JWT and pre-confirmation activation remain open.
6. **9:00–10:30 — Automated controls.** Run:
   ```powershell
   python red_team/live_tests/run_isolated_audit_tests.py
   ```
   Expected: 16/16 PASS on SQLite `:memory:`. Clarify that this is a test database, not PostgreSQL or a live deployment.
7. **10:30–11:30 — Coverage and static analysis.** Open `reports/security_compliance_matrix.md`; show NOT TESTED rows. Show latest Bandit and pip-audit results and explain advisories are not automatic proof of exploitability.
8. **11:30–12:30 — Handover and conclusion.** Open `reports/blue_team_security_handoff.md` and the final PDF. State the unresolved MFA/JWT, email activation, missing throttle migration, dependency, and cart quantity issues. Conclude that SecureShop is not production-ready based on this evidence.

## Expected results and guardrails

- Naive tests should report **7 PASS**; any failure stops the demo from claiming the scenario reproduced.
- SecureShop in-memory suite should report **16/16 PASS**; the suite does not prove live defense.
- Do not use the BAT menu's live test/start options without a separate disposable clone, synthetic role accounts, and explicit runtime authorization.
- Do not demonstrate real accounts, payment data, the shared PostgreSQL database, or public network exposure.
- If an expected result differs, label it **INCONCLUSIVE** and preserve the generated output; do not edit prior evidence.

