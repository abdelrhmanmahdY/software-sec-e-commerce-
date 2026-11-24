# Threat Model — SecureShop

STRIDE-based, tied to the actual application (routes, models, roles). Date: 2026-11-25.

> **Evidence boundary:** this threat model is now backed by **live testing** against the Docker/HTTPS/PostgreSQL stack (`live_tests/run_regression.py`, every row *DEFENSE HELD*), the 22-test Django suite, and the in-memory verifiers. The previously-open findings are re-verified **resolved** (see §"Executed abuse cases"). For the full topic-by-topic defense map see `SUBMISSION_STATUS_2026-11-25.md` and `security_compliance_matrix.md`.

## Assets
- User accounts and credentials (`auth_user`, password hashes).
- Store credit balances (`users_userprofile.store_credit`).
- Orders and order history (`orders_order`).
- Product catalog & pricing integrity (`products_product`).
- Coupons / discount integrity (`users_coupon`, `users_couponusage`).
- Admin control plane (Django admin, dashboard staff pages).
- Audit log (`audit_auditlog`) — integrity of the accountability record.

## Roles / actors
- **Anonymous visitor** — can browse the catalog, register, log in.
- **Customer** — owns a cart, places orders with store credit, manages own profile.
- **Staff** — manages products, users, orders via the dashboard.
- **Admin (superuser)** — full Django admin.
- **Attacker variants** — unauthenticated, authenticated customer (abusing own session), malicious staff.

## Trust boundaries
1. Browser ↔ nginx (TLS termination).
2. nginx ↔ Django/gunicorn (private network).
3. Django ↔ PostgreSQL.
4. Session/JWT identity boundary (client cannot be trusted for identity or price).

## Entry points
See `secureshop_tests/endpoint_map.md`. Key sensitive ones: `/api/auth/login|logout`, `/api/orders/*`, `/api/carts/orders/checkout/`, `/dashboard/newsletter/signup/`, `/api/docs/`, `/admin/*`, `/dashboard/*`.

## STRIDE mapping (controls verified live, 2026-11-25)
| Element | Threat | Example | Verified state |
|---|---|---|---|
| Login / JWT | **S**poofing | Password-only token when TOTP is enabled | **Mitigated** — enrolled account, password only → **401**; a valid 6-digit code is required (then 200). Password lockout → 429. |
| Cart / Checkout | **T**ampering | Client changes quantity/price | **Mitigated** — order price is server-side (serializer read-only); client $0.01 → **charged $604.99** live; over-stock rejected at add and update. |
| Orders API | **T**ampering / **I**nfo disclosure | IDOR to others' orders | **Mitigated** — `get_queryset` owner-scoped; `GET /orders/3/` as another user → **404** (live). |
| Coupons | **T**ampering | Reuse / stack discounts | **Mitigated** — `CouponUsage` unique constraint; second redemption → **400 "already used"** (live). |
| Auth tokens | **E**levation / replay | Reuse refresh after logout | **Mitigated** — logout blacklists the refresh token; reuse → **401** (live). |
| All actions | **R**epudiation | Deny performing an action | **Mitigated** — `AuditLog` records actor/IP/old→new; secrets redacted; admin append-only. |
| Admin / staff pages | **E**levation | Non-staff reaching admin | **Mitigated** — non-staff → audited **403**; `/api/docs/` → 403 (live). |
| Transport | **I**nfo disclosure | Sniffing cookies/credentials | **Mitigated** — nginx TLS 1.2/1.3; Secure/HttpOnly/SameSite cookies; 80→301→443. (HSTS currently 0 — raise for production.) |
| API docs | **I**nfo disclosure | Schema exposure | **Mitigated** — `/api/docs/` behind `IsAdminUser` → 403 for non-admin (live). |
| Checkout | **D**oS / integrity | Race / oversell | **Mitigated at checkout** — atomic `select_for_update` on items/coupon/profile re-checks stock and credit. (`add_cart_quantity` itself is unlocked — optional hardening.) |

## Executed abuse cases and status (2026-11-25)

- **Naive Shop V1–V7:** all seven reproduced against loopback with request/response evidence — the intentionally vulnerable baseline.
- **SecureShop — live (Docker/HTTPS/PostgreSQL):** `run_regression.py` ran every equivalent attack and each was **DEFENSE HELD** (IDOR→404, price→403, lockout→429, refresh-after-logout→401, docs→403, unauth cart→403). Independent live checkout: client price ignored, coupon replay rejected, newsletter codes random.
- **SecureShop — in-memory verifiers:** password-only JWT for a TOTP-enabled account → 401; every signup route creates an inactive, unconfirmed user; coupon replay, forged-cookie denial, CSRF 403, checkout invariants all confirmed.
- **SecureShop unit suite:** **22/22** tests passed (lockout, refresh blacklist, IDOR, role checks, server-side price, cart stock limits, audit behavior, email confirmation).

## Residual risks / to confirm
- MFA enrolment is **opt-in** (enforced once enabled). Consider requiring TOTP for staff/admin, and enable it on a demo account for the live demo.
- `add_cart_quantity` is not `select_for_update`-locked — a true concurrent race could transiently overshoot stock before the atomic checkout rejects it (optional hardening).
- HSTS is 0; set `SECURE_HSTS_SECONDS` > 0 for a production profile. Database backups (SEC-07) not yet automated.
- Dependency scan previously reported advisories across several packages — re-run `pip-audit` and patch before final submission.
- SQL injection / XSS are mitigated by the ORM and template auto-escaping by design; not exhaustively fuzzed (outside the lab scope).

> **Resolved since the 2026-11-22 draft:** password-only JWT bypass, missing `AuthThrottle` migration, signup-active-before-confirmation, and the reported cart off-by-one are all **re-verified fixed/not-reproducible** on the current build.
