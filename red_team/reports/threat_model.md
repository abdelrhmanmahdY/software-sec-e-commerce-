# Threat Model — SecureShop

STRIDE-based, tied to the actual application (routes, models, roles). Date: 2026-11-22.

> **Current evidence boundary:** this threat model is analytical, not proof of controls. Current execution evidence is limited to disposable Django tests and in-memory SQLite. Live HTTPS, Docker, and shared PostgreSQL were not tested. See `security_compliance_matrix.md` for current results; the status table below supersedes older summary claims.

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

## STRIDE mapping (observed controls and gaps)
| Element | Threat | Example | Observed state |
|---|---|---|---|
| Login / JWT | **S**poofing | Password-only token when TOTP is enabled | In-memory test confirmed usable JWT issuance without TOTP. Password lockout unit tests pass; TOTP verification fails on clean migrations because `audit_auththrottle` is absent. |
| Cart / Checkout | **T**ampering | Client changes quantity/price | Unit test for order-item client price/status passed. Cart add accepted quantity 3 as quantity 4 despite stock 2; checkout rejected it without changing stock/credit/order count. |
| Orders API | **T**ampering / **I**nfo disclosure | IDOR to others' orders | Owner-scoping and customer mutation tests passed in the in-memory Django suite; no live deployment retest. |
| Coupons | **T**ampering | Reuse / stack discounts | In-memory checkout accepted one synthetic coupon redemption and rejected replay without changing checked state. |
| Auth tokens | **E**levation / replay | Reuse refresh after logout | Refresh-blacklist unit test passed. Password-only JWT bypass for TOTP-enabled account remains open. |
| All actions | **R**epudiation | Deny performing an action | Audit unit tests passed for actor/IP/change data and password redaction; live request correlation NOT TESTED. |
| Admin / staff pages | **E**levation | Non-staff reaching admin | In-memory unauthenticated admin redirect and role tests passed; not a live deployment retest. |
| Transport | **I**nfo disclosure | Sniffing cookies/credentials | TLS, HSTS and live cookie flags NOT TESTED. |
| API docs | **I**nfo disclosure | Schema exposure | In-memory unauthenticated `/api/docs/` request returned 403. |
| Checkout | **D**oS / integrity | Race / oversell | Stock rejection and state invariance tested in SQLite memory. PostgreSQL race behavior NOT TESTED. |

## Executed abuse cases and status

- **Naive Shop V1–V7:** all seven reproduced against loopback with request/response evidence. This verifies the intentionally vulnerable lab, not SecureShop.
- **SecureShop in-memory:** password-only JWT for a TOTP-enabled account and activation before email confirmation were confirmed. Coupon replay, unauthenticated admin/docs denial, forged identity-cookie denial, CSRF rejection, and selected checkout state invariants were verified in disposable fixtures.
- **SecureShop unit suite:** 16/16 tests passed in SQLite `:memory:` for lockout, refresh blacklist, IDOR, role checks, order price/status handling, and audit behavior.
- **Live SecureShop (Docker/HTTPS/PostgreSQL): NOT TESTED.** Do not promote historical results as current.

## Residual risks / to confirm
- JWT login does not enforce TOTP for an enrolled account.
- HTML `/signup/` activates an unconfirmed account.
- `AuthThrottle` has no committed migration; TOTP verification errors on a freshly migrated database.
- Dependency scan reported advisories across 14 packages.
- Cart add increments a new item one extra unit and accepts more than available stock; checkout later rejects over-stock orders.
- Live TLS/header settings, SQL injection, XSS, concurrent checkout races, and full payment-workflow bypass are NOT TESTED.
- A development certificate may be self-signed; no current TLS assessment was performed.
