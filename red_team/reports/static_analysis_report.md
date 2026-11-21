# Static Analysis Report — Bandit (SAST) + pip-audit (SCA)

Date: 2026-11-22. Tools run from the Red Team venv against the project source/dependencies.

> Static analysis finds code/dependency patterns. It is **not** proof of a remotely exploitable vulnerability — each item is reviewed below.

## 1. Bandit (Python SAST)
Command: `bandit -r . -x ./.venv,./red_team,./staticfiles,./software-sec-e-commerce-,./naive_shop,./media -f json`.
Raw output: `bandit_results.json`.

**Result: 5 issues, all LOW severity / medium confidence, all non-exploitable.**

| Test | File:line | Bandit text | Review |
|---|---|---|---|
| B105 | `audit/tests.py:31` | "hardcoded password: 'wrong'" | Test fixture string. **False positive.** |
| B105 | `audit/tests.py:40` | "hardcoded password: 'x'" | Test fixture string. **False positive.** |
| B105 | `audit/tests.py:50` | "hardcoded password: 'bad'" | Test fixture string. **False positive.** |
| B105 | `config/settings.py:35` | "hardcoded password: 'insecure-dev-only-key'" | Dev-only `SECRET_KEY` fallback, used **only when `DEBUG=True`**; production raises `ImproperlyConfigured`. **Not exploitable.** |
| B105 | `dashboard/views.py:170` | "hardcoded password: ''" | Empty-string default in a form field, not a credential. **False positive.** |

**Conclusion:** no actionable Bandit finding in the application code.

## 2. pip-audit (dependency / SCA)
Command: `pip-audit -f json`. Raw output: `pip_audit.json`.

**Result: 15 of 89 installed packages have known advisories** (the pinned `requirements.txt` versions are behind current security releases). This is a real **Vulnerable & Outdated Components** finding (OWASP A06), though exploitability depends on how each package is used.

| Package | Pinned | Advisories (count) | Note |
|---|---|---|---|
| django | 5.2.4 | many | Framework — upgrade to the latest 5.2.x patch is important |
| djangorestframework | 3.16.0 | several | API layer — upgrade |
| cryptography | 45.0.5 | several | TLS/crypto — upgrade |
| pyjwt | 2.10.1 | several | JWT auth — upgrade |
| pillow | 11.3.0 | many | Image handling — upgrade (image upload surface) |
| requests / urllib3 / idna / certifi | pinned | several | HTTP client chain — upgrade |
| gunicorn | 21.2.0 | few | WSGI server — upgrade |
| sqlparse / graphql-core / scapy / python-dotenv / setuptools | pinned | few | upgrade where used |

**Severity (estimated): Medium.** Many advisories are DoS or edge-case; a few (framework, crypto, image) matter more. None was shown to be remotely exploitable in this assessment — this is a **patch-hygiene** finding.

**Recommendation (Blue Team):**
1. Bump `requirements.txt` to current patched versions (start with django, djangorestframework, cryptography, pyjwt, pillow, requests/urllib3, gunicorn).
2. Re-run `pip-audit` until clean.
3. Add dependency scanning to CI so this is caught automatically.

## How to reproduce
```
.venv\Scripts\bandit -r . -x ./.venv,./red_team,./staticfiles,./software-sec-e-commerce-,./naive_shop,./media -f json -o red_team/reports/bandit_results.json
.venv\Scripts\pip-audit -f json -o red_team/reports/pip_audit.json
```
