# Threat Model — SecureShop

STRIDE-based, tied to the actual application (routes, models, roles). Date: 2026-11-22.

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

## STRIDE mapping (with current defenses)
| Element | Threat | Example | Defense in current build |
|---|---|---|---|
| Login / JWT | **S**poofing | Credential stuffing, brute force | Lockout (429) + DRF throttling + audit |
| Cart / Checkout | **T**ampering | Client sets price/total | Server reads `product.price`; `price` read-only |
| Orders API | **T**ampering / **I**nfo disclosure | IDOR to others' orders | `get_queryset` owner scoping → 404 |
| Coupons | **T**ampering | Reuse / stack discounts | `CouponUsage` unique `(user,coupon)` |
| Auth tokens | **E**levation / replay | Reuse refresh after logout | Token blacklist on logout |
| All actions | **R**epudiation | Deny performing an action | `audit` app logs actor/IP/action |
| Admin / staff pages | **E**levation | Non-staff reaching admin | `IsStaff` / `@staff_required` / admin login gate |
| Transport | **I**nfo disclosure | Sniffing cookies/creds | HTTPS, HSTS-ready, Secure+HttpOnly cookies |
| API docs | **I**nfo disclosure | Schema exposure | `public=False`, `IsAdminUser` |
| Checkout | **D**oS / integrity | Race / oversell | `transaction.atomic` + `select_for_update` + stock check |

## Abuse cases tested
Client price tampering, coupon reuse, order IDOR, checkout without payment, login brute force, token replay, unauthenticated admin access — all **blocked** in the current build (see the penetration test report and regression results).

## Residual risks / to confirm
- MFA/TOTP not enforced on seeded accounts (groundwork present).
- Self-signed dev certificate (production should use a trusted CA).
- CRLF line endings in Blue Team shell scripts (build/run blocker, not a security flaw).
