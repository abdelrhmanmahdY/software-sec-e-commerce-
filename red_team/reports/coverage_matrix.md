# Security Coverage Matrix — Red Team contribution

One row per course topic (PDF item 3). This is the **Red Team** contribution; the Blue Team fills the "Defense implemented / Code location" columns as they build.

**Legend (Defense status):**
- `IMPLEMENTED & VERIFIED` — present and confirmed by test.
- `IMPLEMENTED, NOT VERIFIED` — present in code, not yet tested.
- `MISSING` — no defense found.
- `N/A` — not applicable to SecureShop.
- `NOT TESTED` — not yet attempted.

> Every "Test result" below is **NOT TESTED** today — the Blue app is unfinished. Severities are DREAD estimates.

| Course Topic | Attack Scenario (SecureShop) | Feature | Entry Point | Root Cause (hypothesized) | Defense Status | Code Location | Test Result | Evidence |
|---|---|---|---|---|---|---|---|---|
| Client-side trust (Lab 1) | Tamper price/total on order/checkout | Cart/Orders | `/api/orders/order-items/`, checkout | Server trusts client price (H6) | NOT TESTED | `orders/serializers.py:6-9` | NOT TESTED | — |
| Business rules — coupons (Lab 2.1) | Reuse/predict/stack coupons | Coupons | checkout, newsletter | No used-coupon tracking (H3, H4, H23) | NOT TESTED | `carts/views.py:100-109` | NOT TESTED | — |
| Exceptional input (Lab 2.2) | Negative/huge/over-long/empty input | Cart, Registration | `cart/add`, `update-quantity`, signup | Weak validation; error leakage (H7, H8) | NOT TESTED | `carts/views.py:36,77` | NOT TESTED | — |
| Workflow validation (Lab 2.3) | Pay-less / replay confirmation / status choice | Checkout, Orders | checkout endpoints, order create | No server-side state machine (H1, H2, H17) | NOT TESTED | `carts/views.py:95`, `orders/views.py:19` | NOT TESTED | — |
| Authentication (Lab 3) | Identity forge / brute force / enumeration | Login, 2FA | login, confirm | Client-controlled identity; no lockout (H11-H14, H19) | NOT TESTED | `dashboard/views.py:102`, `settings.py` | NOT TESTED | — |
| Access control / AuthZ (Lec 2-3) | IDOR; staff escalation; non-admin writes | Orders, Admin, Category | `/api/orders/...`, dashboard | Missing object/role checks (H5, H9, H15, H16) | NOT TESTED | `orders/views.py:9-17` | NOT TESTED | — |
| Password storage (Lec 4) | Offline cracking if hashes leak | Auth | DB | Django PBKDF2 vs Argon2/bcrypt (H20) | IMPLEMENTED, NOT VERIFIED | `settings.py` (default) | NOT TESTED | — |
| Session security (Lec 5) | Token replay after logout | JWT | `/api/...` | No token blacklist (H19) | NOT TESTED | `config/urls.py:38` | NOT TESTED | — |
| Non-repudiation / logging (Lec 2) | Actions not logged | All | — | No audit logging (H21) | NOT TESTED | (needs final build) | NOT TESTED | — |
| Behavioral anomaly detection (Lab 4) | Validate control / replay | Login | login | Defense — likely absent | N/A | — | NOT TESTED | — |
| Location/Time/Passkey/TOTP (Lab 5) | Validate controls | Login/MFA | login | Defense — likely absent | N/A | — | NOT TESTED | — |
| Misconfiguration (optional) | DEBUG/hosts/schema exposure | Config | settings, `/api/docs/` | Permissive config (H22) | NOT TESTED | `settings.py:10-12` | NOT TESTED | — |
| Injection — SQLi/XSS (optional) | Not covered by a lab | — | — | — | N/A (optional) | — | NOT TESTED | — |

## How to update this matrix during the testing window
For each row, after an authorized test: set **Test result** to CONFIRMED / INCONCLUSIVE / PASS (secure), fill **Defense Status** and **Code Location** from the Blue Team, and link the **Evidence** file.
