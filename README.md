# SecureShop — CET431 Software Security E-Commerce Project

SecureShop is a hardened Django e-commerce web application built for **CET431 – Software Security (Fall 2026)**. It implements full e-commerce functionality (catalogue, cart, coupons, newsletter, store-credit checkout, user profiles, and admin dashboard) with application-level security defenses, HTTPS/TLS termination, and AAA (Authentication, Authorization, Accounting).

---

## Quick Start (Docker Compose — Recommended)

**Requirements:** Docker and Docker Compose.

```bash
git clone https://github.com/abdelrhmanmahdY/software-sec-e-commerce-.git
cd software-sec-e-commerce-
chmod +x scripts/setup-local-tls.sh scripts/generate_certs.sh

# Build and start PostgreSQL, Django (Gunicorn), and Nginx (HTTPS)
make up

# Apply migrations and seed demo accounts + sample data
make migrate
make seed

# Run Django system checks and unit tests
make check
make test
```

Once running, open **`https://localhost`** (accept the self-signed certificate warning, or run `make tls-setup` if `mkcert` is installed).

### Useful Make Commands
- `make up` — build and start all containers (`certs`, `db`, `web`, `nginx`)
- `make down` — stop containers
- `make logs` — follow container logs
- `make migrate` — run Django migrations
- `make seed` / `make reset` — seed or clear & reseed demo data
- `make check` — run `manage.py check` and migration checks
- `make test` — run the Django test suite (`SECURE_SSL_REDIRECT=False`)

---

## Test Accounts

Seeded by `make seed` (`users/management/commands/seed_data.py`):

| Role | Username | Password | Initial Store Credit |
|---|---|---|---|
| Admin / Superuser | `admin` | `Admin!2026#Secure` | `$500.00` |
| Staff | `staff` | `Staff!2026#Secure` | `$0.00` |
| Customer | `customer` | `Customer!2026#Secure` | `$500.00` |

### Key URLs
- **Storefront / Dashboard:** `https://localhost/`
- **Django Admin:** `https://localhost/admin/`
- **Audit Log (Staff only):** `https://localhost/dashboard/audit/`
- **API Docs / Swagger (Admin only):** `https://localhost/api/docs/`
- **Local Email Inbox (Mailpit — account confirmation):** `http://localhost:8025/`

---

## Architecture Overview

```
Browser / API Client
        │  HTTPS (TLS 1.2 / 1.3, port 443; port 80 -> 301 HTTPS)
        ▼
  ┌───────────┐
  │   Nginx   │  TLS termination, HSTS-ready, overwrites X-Forwarded-For,
  │  (proxy)  │  serves /media/ read-only with X-Content-Type-Options: nosniff
  └─────┬─────┘
        │  HTTP (internal Docker network only, port 8000 not exposed)
        ▼
  ┌───────────┐
  │  Django   │  Gunicorn (unprivileged UID 1000), WhiteNoise static files
  │  + DRF    │  Apps: users | products | carts | orders | dashboard | audit
  └─────┬─────┘
        │  PostgreSQL protocol (internal Docker network)
        ▼
  ┌───────────┐
  │PostgreSQL │  postgres:16-alpine (persistent volume: postgres_data)
  └───────────┘
```

### Django Applications
- **`users`**: Custom `UserProfile` (`store_credit`, `email_confirmed`), `Coupon`, `CouponUsage` (single-use enforcement), `NewsletterSubscriber`, and RBAC permission classes (`IsStaff`, `IsStaffOrCreateReadOnly`).
- **`products`**: `Category` and `Product` models with search, filtering, and pagination.
- **`carts`**: Session/user `Cart`, `CartItem`, and atomic `CheckoutView` (validates stock, single-use coupons, and store credit).
- **`orders`**: `Order`, `OrderItem`, owner-scoped `OrderViewSet` (prevents IDOR), server-side pricing, and atomic API `CheckoutView`.
- **`dashboard`**: Web UI for storefront, cart, profile/settings, email confirmation, newsletter signup, and staff-only management/audit pages.
- **`audit`**: `AuditLog` model, signals, middleware, brute-force lockout (`AuditedTokenObtainPairView`, `429` after 5 failures), and JWT refresh-token blacklisting (`LogoutAPIView`).

### Security Controls Summary
- **Transport (TLS):** Nginx terminates TLS 1.2/1.3 with self-signed certs (`scripts/generate_certs.sh`) and redirects all HTTP to HTTPS; Django enforces `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE`. See [docs/TLS_AAA.md](docs/TLS_AAA.md).
- **Authentication & Sessions:** PBKDF2 password hashing, per-IP/username login lockout (`429`), JWT refresh-token blacklisting on logout, signed email-confirmation tokens.
- **Authorization:** Object-level ownership scoping on orders (blocks IDOR), `@staff_required` / `IsAdminUser` on admin pages and `/api/docs/`.
- **Business Logic & Input Validation:** Server-side price lookup, atomic `select_for_update()` store-credit & stock checks, single-use `CouponUsage` constraint, cryptographically random newsletter coupons (`secrets.token_hex`), generic error responses, Django ORM (SQLi-safe), template auto-escaping + `textContent` (XSS-safe), and `CsrfViewMiddleware`.
- **Accounting:** All logins, lockouts, logouts, access denials (`403`), and model changes are recorded in `AuditLog` without logging passwords.

---

## Red Team & Documentation
- **Security Coverage Matrix:** `red_team/reports/coverage_matrix.md`
- **Live Tests & Evidence:** `red_team/live_tests/`, `red_team/evidence/`
- **Isolated Lab Demos (Naive vs. Defended):** `red_team/labs/`
- **TLS & AAA Guide:** `docs/TLS_AAA.md`
