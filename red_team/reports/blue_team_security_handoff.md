# Red Team → Blue Team Security Handoff

**Prepared:** 2026-11-22  
**Repository:** `D:\software-sec-e-commerce-`  
**Branch / HEAD reviewed:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`  
**Boundary:** Findings only. No Blue Team source, configuration, or database changes were made.

## Confirmed findings requiring owner review

### RT-BT-01 — JWT login bypasses TOTP enforcement

- **Priority:** High — authentication assurance bypass for accounts configured to require TOTP.
- **Evidence:** Current-checkout isolated Django test in [`phase1_inmemory_registration_mfa_20261122.md`](../evidence/review/phase1_inmemory_registration_mfa_20261122.md): a TOTP-enabled synthetic user submitted password-only credentials to `/api/auth/login/`; the endpoint returned HTTP 200 with an access token, and the token accessed `/api/orders/orders/` with HTTP 200.
- **Source locations:** [`audit/views.py`](../../audit/views.py) delegates successful login to the default token view; [`config/urls.py`](../../config/urls.py) exposes the JWT login route. The tested path did not require a TOTP value.
- **Historical corroboration:** [`backend_results.json`](../evidence/review/backend_results.json) has a prior PostgreSQL transaction result `DB-MFA-JWT-bypass`, with rollback verified.
- **Recommended Blue Team action:** Require completion of the enrolled second factor before issuing a usable access/refresh token, or use a short-lived pre-authentication challenge token that cannot access ordinary protected APIs.
- **Retest acceptance:** With a disposable TOTP-enabled account, password-only login must not yield an access token usable on protected APIs; valid password plus valid second factor must still permit the intended flow; wrong, missing, replayed, and expired codes must fail. Confirm database/session state and preserve redacted request/response evidence.

### RT-BT-02 — `/signup/` activates an unconfirmed account

- **Priority:** High — account-confirmation requirement can be bypassed on one registration route.
- **Evidence:** Current-checkout isolated Django test in [`phase1_inmemory_registration_mfa_20261122.md`](../evidence/review/phase1_inmemory_registration_mfa_20261122.md): `POST /signup/` returned HTTP 302 and created `is_active=True` with `email_confirmed=False`; `/dashboard/signup/` and `/api/users/signup/` created inactive accounts.
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
