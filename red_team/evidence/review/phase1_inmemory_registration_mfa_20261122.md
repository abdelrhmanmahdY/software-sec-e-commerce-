# Phase One: Isolated Registration and MFA Checks

- **Observed:** 2026-11-22, runtime log times 04:15 and 04:17 (local timezone not established)
- **Repository:** `D:\software-sec-e-commerce-`
- **Branch / HEAD:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`
- **Execution:** Django `TestClient`; SQLite `:memory:` database; synthetic accounts only
- **Network / persistent database:** None. No browser, running web service, PostgreSQL, or external host was contacted.

The test process set `DATABASE_URL=sqlite:///:memory:` and used Django's PBKDF2 hasher override because the repository virtual environment does not contain the configured `bcrypt` dependency. These checks do not validate the current bcrypt implementation or real email delivery. All fixture rows, including the test TOTP secret, existed only in the process's in-memory database and were discarded at exit.

## Registration confirmation-path consistency

Synthetic form/API registrations were submitted through Django's request client. The password and other test credentials are intentionally not retained.

| Route | Request / result | Database state observed immediately after |
|---|---|---|
| `POST /signup/` | Form fields posted; HTTP 302 | `User.is_active=True`; related profile `email_confirmed=False` |
| `POST /dashboard/signup/` | Same form workflow; HTTP 302 | `User.is_active=False` |
| `POST /api/users/signup/` | JSON registration; HTTP 201 | `User.is_active=False` |

**Result:** The `/signup/` HTML route enables the account before email confirmation, while the dashboard form and API routes create inactive accounts. This is a route inconsistency confirmed against the current source checkout in an in-memory Django test; it was not a browser or live-service test.

Relevant source: [`users/views.py`](../../../users/views.py), [`users/serializers.py`](../../../users/serializers.py), and [`dashboard/views.py`](../../../dashboard/views.py).

## TOTP enforcement on JWT login

An in-memory user fixture was created with `totp_enabled=True`. The test posted only username and password to `POST /api/auth/login/`; no TOTP value was submitted. It then used the returned access token to request the protected order-list endpoint.

| Check | Observed result |
|---|---|
| `POST /api/auth/login/` with password only | HTTP 200 |
| Access token returned | Yes |
| TOTP submitted | No |
| `GET /api/orders/orders/` with that token | HTTP 200 |

**Result:** TOTP-enabled users can obtain a JWT and access a protected API without submitting a second factor. The test did not retain the token or test other accounts. This is a current-checkout Django request-client result using only in-memory data, not a browser/live-service test.

Relevant source: [`audit/views.py`](../../../audit/views.py), [`config/urls.py`](../../../config/urls.py), and [`users/models.py`](../../../users/models.py).

## Limitations

- Django `TestClient` exercises Django's request stack but is not evidence of TLS, proxy behavior, browser UX, or a separately running deployment.
- The account-confirmation email was captured only by Django's in-memory mail backend; no real delivery was attempted.
- The test-specific PBKDF2 override bypassed the configured custom bcrypt hasher. Password-hasher availability and behavior remain a separate release blocker to resolve with the Blue Team owner.
- The requests were low-impact and used disposable in-memory fixtures; no existing data was changed.
