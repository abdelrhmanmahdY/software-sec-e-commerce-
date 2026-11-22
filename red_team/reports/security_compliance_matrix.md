# Official Security Requirements Compliance Matrix

**Audit date:** 2026-11-22  
**Sources:** attached CET431 specification, `red_team/labs/lab1_*` through `lab5_*`, existing SecureShop Red Team reports and live evidence.

## Matrix

| Course topic | Applicable features | Naive scenario | SecureShop defense / code | Manual/automated evidence | Status |
|---|---|---|---|---|---|
| Excessive client-side trust (Lab 1) | Cart, checkout, order items | Browser supplies price/total/status | Server reads catalog price and restricts status/price | Existing live regression test H6 | IMPLEMENTED & VERIFIED for tested order-item price |
| Business-rule enforcement (Lab 2.1) | Coupons, checkout | Coupon replay/stacking | `CouponUsage` unique `(user,coupon)`; coupon validation in checkout | Unit/code evidence exists; live reuse not completed this audit | IMPLEMENTED, NOT VERIFIED |
| Exceptional input (Lab 2.2) | Registration, cart quantities, profile | Over-long/negative/empty input | Django forms/serializers and quantity checks need live verification | No complete browser or malformed-input evidence | NOT TESTED |
| Workflow validation (Lab 2.3) | Checkout, confirmation, order state | Skip payment or replay confirmation | Atomic checkout, store-credit and stock checks | Source exists; no live workflow or DB delta completed | IMPLEMENTED, NOT VERIFIED |
| Authentication identity and 2FA (Lab 3) | Login, 2FA, sessions | Client-controlled identity or weak MFA | Server-side Django authentication, TOTP fields/routes exist | Seed/TOTP state not enforced test; browser login passed | PARTIAL |
| Brute-force protection (Lab 3/AAA) | Login, 2FA | Unlimited password/code attempts | Lockout backend and DRF throttling | Unit test suite and existing lockout evidence; live browser/API result has prior inconclusive flag | IMPLEMENTED & VERIFIED by automated test, live recheck INCONCLUSIVE |
| Authorization / IDOR | Orders, profiles, cart, admin | Read/edit another user's data | Owner-scoped order query, staff/admin guards | Existing live H5 regression passed; browser role checks passed for Django newsletter | IMPLEMENTED & VERIFIED in sampled areas |
| Least privilege | Customer, staff, admin | Customer reaches staff/admin operations | `is_staff`, `is_superuser`, staff decorators, Django admin permissions | Browser: customer denied, staff got 403 at Django newsletter, admin got changelist | IMPLEMENTED & VERIFIED |
| Password storage | Accounts | Offline hash cracking | Django password hasher/PBKDF2 | Source/config only | IMPLEMENTED, NOT VERIFIED |
| Session security | Login/logout/protected pages | Replay or steal session/JWT | HttpOnly/SameSite/Secure cookies; 30-minute sliding session; refresh blacklist | Config/source exists; logout browser observed; refresh replay not rerun by this audit | IMPLEMENTED, NOT VERIFIED |
| Information leakage | Login, errors, API docs | Verbous errors/docs leak internals | Generic error responses and admin-only Swagger | Existing H22 live 403; customer/unauth admin URL checks | PARTIAL |
| Fail secure | Checkout, auth, authorization | Partial failure creates order/grants access | Transactions and permission checks | Unit/source evidence; malformed live workflows incomplete | PARTIAL |
| Accounting / non-repudiation | Logins, 403s, models | Critical actions lack audit trail | `AuditLog`, middleware and signals | 73 live audit rows observed and unit tests create audit events | IMPLEMENTED & VERIFIED at implementation level |
| Behavioral anomaly detection (Lab 4) | Login risk | Replay typing signature | No implementation found | No feature in source | NOT APPLICABLE / absent |
| Location/time/passkeys (Lab 5) | Login/MFA | Bypass location/time/passkey policy | TOTP groundwork only; no location/passkey/time gate found | Code fields/routes exist, no live TOTP enrollment/MFA enforcement test | PARTIAL / not a standalone passkey/location control |
| SQL injection | Search/API/database reads | Inject SQL | Django ORM parameterized queries | Automated/live claims in docs, not independently rerun in this audit | IMPLEMENTED, NOT VERIFIED |
| XSS | Search/profile/newsletter | Inject script/DOM HTML | Template escaping and `textContent` claim | Source claim only, no live payload test this audit | IMPLEMENTED, NOT VERIFIED |
| CSRF | State-changing forms/JWT | Forged state change | Django CSRF middleware; secure cookies | Source/config evidence; no live forged request test this audit | IMPLEMENTED, NOT VERIFIED |
| TLS and transport | Login/admin/API | Credential/cookie sniffing | nginx TLS, secure session/CSRF cookies | Browser reached HTTPS, application root and admin under HTTPS | IMPLEMENTED & VERIFIED |
| Misconfiguration | Debug/API docs/admin | Expose schema or internals | `DEBUG=False`, admin permissions, Swagger `IsAdminUser` | Live unauth/role checks | IMPLEMENTED & VERIFIED for admin newsletter and API docs evidence |

**Security evidence caveat:** Existing reports contain several unverified or contradictory claims. They are not counted as live-verified unless a current browser run, database check, or 16-test suite output independently supports them.

