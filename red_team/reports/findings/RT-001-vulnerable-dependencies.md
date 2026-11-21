# RT-001 — Vulnerable & Outdated Dependencies

- **Severity:** Medium (estimated; DREAD D2 R3 E1 A2 D3 = 11)
- **Category:** OWASP A06 Vulnerable & Outdated Components / SCA
- **Affected:** `requirements.txt` (runtime dependencies)
- **Attacker role / preconditions:** varies per advisory; none shown remotely exploitable in this assessment
- **Status:** CONFIRMED (static, via pip-audit) · **Not** demonstrated as a live exploit

## Description
`pip-audit` reports **15 of 89 installed packages** carry known security advisories because `requirements.txt` pins versions behind current patched releases. Notable: `django 5.2.4`, `djangorestframework 3.16.0`, `cryptography 45.0.5`, `pyjwt 2.10.1`, `pillow 11.3.0`, `requests 2.32.4`, `urllib3 2.5.0`, `gunicorn 21.2.0`.

## Evidence
- `red_team/reports/pip_audit.json` (raw)
- `red_team/reports/static_analysis_report.md` (reviewed table)

## Technical root cause
Dependencies are pinned and not refreshed; no automated SCA in CI.

## Impact
Depends on the advisory and usage. Framework (django/DRF), crypto (cryptography/pyjwt) and image parsing (pillow, an upload surface) carry the most weight; several others are DoS/edge-case. Confirmed impact here: **none demonstrated** (static finding). Theoretical impact: exposure to published CVEs if an affected code path is reachable.

## Recommended remediation
1. Upgrade to current patched versions, prioritising django, djangorestframework, cryptography, pyjwt, pillow, requests/urllib3, gunicorn.
2. Re-run `pip-audit` until clean.
3. Add `pip-audit` (or equivalent) to CI to prevent regressions.

## Retest procedure
`.venv\Scripts\pip-audit -f json -o red_team/reports/pip_audit.json` → expect 0 packages with advisories.

## Retest result
NOT RE-TESTED (pending Blue Team upgrade).
