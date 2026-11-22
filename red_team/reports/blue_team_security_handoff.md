# Red Team → Blue Team Security Handoff

**Prepared:** 2026-11-22  
**Repository:** `D:\software-sec-e-commerce-`  
**Branch / HEAD reviewed:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`  
**Boundary:** Findings only. No Blue Team source, configuration, or database changes were made.

## Latest isolated-test update

The current checkout is the user-supplied `main` / `c9776b750677c942410572d1afbf3c786f336b9d`; the branch/HEAD line above is historical. New tests used SQLite `:memory:` and synthetic data only. They confirm RT-BT-01 and RT-BT-02 below and add:

### RT-BT-04 — TOTP verification throttle table is missing from migrations

- **Priority:** Medium — TOTP verification fails on a clean database before the factor is verified.
- **Evidence:** `verify_inmemory_security_20261122T055710Z.json` records `no such table: audit_auththrottle` after normal migrations. `totp_ip_lockout_20261122T055718Z.json` shows the lockout policy itself works only after test-only schema-editor creation of the missing table.
- **Recommended action:** add and test a migration for `AuthThrottle`; verify fresh install and upgrade paths.
- **Retest acceptance:** with standard migrations only, TOTP verification returns an intentional response rather than a database exception; IP lockout blocks at the configured threshold and another IP is not incorrectly blocked.

### RT-BT-05 — Cart add increments a new item one extra unit

- **Priority:** Low — cart quantity can exceed stock and prevent a valid purchase.
- **Evidence:** `workflow_checks_20261122T055720Z.json`: POST quantity 3 returned quantity 4 while stock was 2; checkout rejected with `Insufficient stock`, with stock/credit/order count unchanged.
- **Recommended action:** create new cart items with the requested quantity without adding an extra default unit; reject or cap requested quantities against available stock.
- **Retest acceptance:** first add of quantity 1 yields 1; boundary quantities are validated; checkout of available stock succeeds and over-stock attempts create no order or credit deduction.

### RT-BT-06 — Dependency advisories in declared requirements

- **Priority:** Medium pending package-specific exploitability review.
- **Evidence:** fresh pip-audit result: 216 advisories across 14 packages in 64 requirements entries; see `evidence/review/pip_audit_20261122T054622318131Z.json`.
- **Recommended action:** review and upgrade to patched compatible releases; rerun tests and pip-audit.

The previous `workflow_checks_20261122T053130Z.json` and `workflow_checks_20261122T053648Z.json` are preserved but do not prove stock validation; see `evidence/review/workflow_checks_correction_20261122.md`. The corrected stock evidence is the 05:37:04 run.

Live HTTPS, Docker, and shared PostgreSQL were not started; no persistent database was changed.

## Confirmed findings requiring owner review

### RT-BT-01 — JWT login bypasses TOTP enforcement

- **Priority:** High — authentication assurance bypass for accounts configured to require TOTP.
- **Evidence:** Latest current-checkout isolated Django evidence [`verify_inmemory_security_20261122T055710Z.json`](../evidence/review/verify_inmemory_security_20261122T055710Z.json) records a TOTP-enabled synthetic user submitting password-only credentials to `/api/auth/login/`; the endpoint returned HTTP 200 with an access token, and the token accessed `/api/orders/orders/` with HTTP 200.
- **Source locations:** [`audit/views.py`](../../audit/views.py) delegates successful login to the default token view; [`config/urls.py`](../../config/urls.py) exposes the JWT login route. The tested path did not require a TOTP value.
- **Historical corroboration:** [`backend_results.json`](../evidence/review/backend_results.json) has a prior PostgreSQL transaction result `DB-MFA-JWT-bypass`, with rollback verified.
- **Recommended Blue Team action:** Require completion of the enrolled second factor before issuing a usable access/refresh token, or use a short-lived pre-authentication challenge token that cannot access ordinary protected APIs.
- **Retest acceptance:** With a disposable TOTP-enabled account, password-only login must not yield an access token usable on protected APIs; valid password plus valid second factor must still permit the intended flow; wrong, missing, replayed, and expired codes must fail. Confirm database/session state and preserve redacted request/response evidence.

### RT-BT-02 — `/signup/` activates an unconfirmed account

- **Priority:** High — account-confirmation requirement can be bypassed on one registration route.
- **Evidence:** Latest current-checkout isolated Django evidence [`verify_inmemory_security_20261122T055710Z.json`](../evidence/review/verify_inmemory_security_20261122T055710Z.json): `POST /signup/` returned HTTP 302 and created `is_active=True` with `email_confirmed=False`; `/dashboard/signup/` and `/api/users/signup/` created inactive accounts.
- **Source locations:** [`users/views.py`](../../users/views.py) invokes `form.save()` on its HTML path. [`dashboard/views.py`](../../dashboard/views.py) and [`users/serializers.py`](../../users/serializers.py) explicitly mark accounts inactive.
- **Recommended Blue Team action:** Consolidate or align all registration entry points so account activation follows the same confirmation policy. Avoid relying on the UI to hide an alternate route.
- **Retest acceptance:** Submit through every HTML and API registration route; before confirmation, login and protected actions must be denied; after valid confirmation, intended login must work. Include duplicate and invalid confirmation cases.

## Build / verification blocker (not a vulnerability finding)

### RT-BT-03 — bcrypt runtime dependency unavailable in the local test environment

- **Priority:** High for release verification.
- **Evidence:** Baseline documented that the custom bcrypt-SHA256/pepper hasher is selected in [`config/settings.py`](../../config/settings.py), but `bcrypt` was absent from the repository virtual environment and not declared in the inspected dependency manifest. The running Docker application reported PBKDF2, so it was not testing current source configuration.
- **Recommended owner action:** Coordinate with the author of the recent hasher change to declare/install the dependency and verify a fresh image; do not silently substitute another hasher in the production configuration.
- **Retest acceptance:** New environment starts; synthetic password hash/verify succeeds; legacy hashes remain verifiable/migratable; current image's active hasher matches the reviewed configuration.

## Scope and evidence caveats

- The new tests used Django's request client and `sqlite:///:memory:` fixtures. They did not contact the running HTTPS service or persistent PostgreSQL database.
- The historical PostgreSQL transaction tests are not current live-deployment evidence; see [`phase_one_attack_evidence.md`](phase_one_attack_evidence.md).
- Red Team has not modified or attempted to fix any of these findings. Blue Team should acknowledge ownership and coordinate a retest window before remediation if shared work is in progress.
