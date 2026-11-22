# Security Coverage Matrix — Red Team contribution

One row per course topic (PDF item 3). This is the **Red Team** contribution; the Blue Team fills the "Defense implemented / Code location" columns as they build.

**Legend (Defense status):**
- `IMPLEMENTED & VERIFIED` — present and confirmed by test.
- `IMPLEMENTED, NOT VERIFIED` — present in code, not yet tested.
- `MISSING` — no defense found.
- `N/A` — not applicable to SecureShop.
- `NOT TESTED` — not yet attempted.

> **Updated 2026-11-22** from `red_team/evidence/live/regression_results.md` (the last live run of `run_regression.py`, executed 2026-11-22 against the hardened build at `https://localhost`). That run, the `naive_shop` attacks, and the Bandit scan were re-verified in this session; rows not covered by any live test keep **NOT TESTED** honestly rather than being marked secure. Severities for still-open rows are DREAD estimates, not measured.

| Course Topic | Attack Scenario (SecureShop) | Feature | Entry Point | Root Cause (hypothesized) | Defense Status | Code Location | Test Result | Evidence |
|---|---|---|---|---|---|---|---|---|
| Client-side trust (Lab 1) | Tamper price/total on order/checkout | Cart/Orders | `/api/orders/order-items/`, checkout | Server trusts client price (H6) | IMPLEMENTED & VERIFIED | `orders/serializers.py` (price read-only, status stripped for customers) | TESTED - DEFENSE HELD | `evidence/live/regression_results.md` (T-H6-price: non-staff set price → 403) |
| Business rules — coupons (Lab 2.1) | Reuse/predict/stack coupons | Coupons | checkout, newsletter | No used-coupon tracking (H3, H4, H23) | IMPLEMENTED, NOT VERIFIED (this round) | `users/models.py` (`CouponUsage` unique constraint) | NOT TESTED this round | H4 confirmed vulnerable in the 2026-11-21 baseline (`reports/live_baseline_report.md`); constraint exists in code but needs a fresh live re-test against the current build |
| Exceptional input (Lab 2.2) | Negative/huge/over-long/empty input | Cart, Registration | `cart/add`, `update-quantity`, signup | Weak validation; error leakage (H7, H8) | NOT TESTED | `carts/views.py` | NOT TESTED | H8 was INCONCLUSIVE in the baseline; still needs an authenticated malformed-request pass |
| Workflow validation (Lab 2.3) | Pay-less / replay confirmation / status choice | Checkout, Orders | checkout endpoints, order create | No server-side state machine (H1, H2, H17) | IMPLEMENTED, NOT VERIFIED (this round) | `carts/views.py` (atomic store-credit + stock check) | NOT TESTED this round | Code read confirms atomic check; not re-driven live this session |
| Authentication (Lab 3) | Identity forge / brute force / enumeration | Login, 2FA | login, confirm | Client-controlled identity; no lockout (H11-H14, H19) | IMPLEMENTED & VERIFIED (lockout) | `config/settings.py` (`LockoutModelBackend`, DRF throttling), `audit/views.py` (JWT blacklist) | TESTED - DEFENSE HELD | `evidence/live/regression_results.md` (T-H13: 429 after repeated fails; T-H19: blacklisted refresh → 401) |
| Access control / AuthZ (Lec 2-3) | IDOR; staff escalation; non-admin writes | Orders, Admin, Category | `/api/orders/...`, dashboard | Missing object/role checks (H5, H9, H15, H16) | IMPLEMENTED & VERIFIED (orders, cart) | `orders/views.py` (`get_queryset` scoped to `request.user`) | TESTED - DEFENSE HELD | `evidence/live/regression_results.md` (T-H5-list/detail: own orders only, other user's order → 404; T-H9: unauth cart update → 403) |
| Password storage (Lec 4) | Offline cracking if hashes leak | Auth | DB | Django PBKDF2 vs Argon2/bcrypt (H20) | IMPLEMENTED, NOT VERIFIED | `settings.py` (Django default PBKDF2) | NOT TESTED | No hash-cracking test performed (would require exporting hashes, out of scope without written approval) |
| Session security (Lec 5) | Token replay after logout | JWT | `/api/...` | No token blacklist (H19) | IMPLEMENTED & VERIFIED | `audit/views.py` (blacklist on logout) | TESTED - DEFENSE HELD | `evidence/live/regression_results.md` (T-H19) |
| Non-repudiation / logging (Lec 2) | Actions not logged | All | — | No audit logging (H21) | IMPLEMENTED, NOT VERIFIED | `audit/` app (login/logout/order events) | NOT TESTED | App exists and is wired into login/logout per code read; log *contents* not independently inspected this session |
| Behavioral anomaly detection (Lab 4) | Validate control / replay | Login | login | Defense — likely absent | N/A | — | NOT TESTED | No anomaly-detection feature found in the code |
| Location/Time/Passkey/TOTP (Lab 5) | Validate controls | Login/MFA | login | TOTP groundwork exists, not enforced | IMPLEMENTED, NOT VERIFIED | `dashboard/views.py` (`totp_setup`, `verify_totp_code`) | NOT TESTED | TOTP can be enabled per-user but isn't enforced on seeded accounts — confirm intended policy with the Blue Team |
| Misconfiguration (optional) | DEBUG/hosts/schema exposure | Config | settings, `/api/docs/` | Permissive config (H22) | IMPLEMENTED & VERIFIED | `config/urls.py` (Swagger `public=False`, `IsAdminUser`) | TESTED - DEFENSE HELD | `evidence/live/regression_results.md` (T-H22: unauth `/api/docs/` → 403) |
| Injection — SQLi/XSS (optional) | Not covered by a lab | — | — | — | N/A (optional) | — | NOT TESTED | Not in scope of the labs; not attempted |

## How to update this matrix going forward
For each row still marked **NOT TESTED**, re-run the matching script in `red_team/live_tests/` against the live app (Docker + browser available), then flip the status to TESTED - DEFENSE HELD / CONFIRMED VULNERABILITY / INCONCLUSIVE and link the fresh evidence file. Do not flip a row to "secure" from a code read alone — only a live test earns that status, per the project's own evidence rule.
