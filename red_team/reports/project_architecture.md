# SecureShop — Project Architecture (Red Team discovery)

**Phase A discovery. Date: 2026-11-22.** Source: read-only inspection of the current repository. This reflects the **hardened** version the Blue Team has shipped (not my earlier baseline).

## 1. Stack
- **Backend:** Django 5.2.4 + Django REST Framework, SimpleJWT (with `token_blacklist`).
- **Frontend:** Django server-rendered templates (`dashboard/templates/`) + vanilla JS `fetch`.
- **Database:** PostgreSQL 16 (Docker). SQLite fallback only if `DATABASE_URL` unset.
- **Serving:** Gunicorn/Django behind **nginx** terminating **TLS (HTTPS)**. `web` container is `expose: 8000` (internal only); nginx publishes `80`/`443`.
- **Config:** `DEBUG=False` in Docker; secrets from env; auto-generated `SECRET_KEY` stored in a volume.

> **Access URL changed:** the app is now at **`https://localhost/`** (self-signed cert), not `http://localhost:8000/`. Plain HTTP redirects to HTTPS (`SECURE_SSL_REDIRECT`).

## 2. Django apps
| App | Responsibility |
|---|---|
| `users` | `UserProfile` (store_credit, email_confirmed, **totp_secret/totp_enabled**), `Coupon`, **`CouponUsage`**, `NewsletterSubscriber`, permissions, TOTP, forms, serializers |
| `products` | `Category`, `Product`; `ProductViewSet` (IsAdminOrReadOnly) |
| `carts` | `Cart`, `CartItem`; add/remove/update/checkout |
| `orders` | `Order`, `OrderItem`; `OrderViewSet` (owner-scoped), `CheckoutView` |
| `dashboard` | Session-based UI: shop, cart, profile, admin pages, newsletter |
| **`audit`** | **AAA Accounting**: `AuditLog` model, middleware, signals, login lockout backend, audited JWT login/logout |

## 3. Authentication (AAA)
- **Two surfaces:** Django session (`/dashboard/...`) and JWT (`/api/...`).
- **Login lockout:** `AUTHENTICATION_BACKENDS = ["audit.backends.LockoutModelBackend"]`; `LOGIN_MAX_FAILURES=5` (user+IP), `LOGIN_MAX_FAILURES_PER_IP=20`, `LOGIN_LOCKOUT_MINUTES=15`. JWT login returns **429** when locked (`audit/views.py:AuditedTokenObtainPairView`).
- **DRF throttling:** `anon 60/min`, `user 300/min`.
- **JWT:** access 15 min, refresh 1 day, rotate + blacklist after rotation; logout blacklists the refresh token.
- **Passwords:** Django PBKDF2; validators incl. min length 10.
- **TOTP:** `users/totp.py` + profile fields — MFA groundwork (verify whether enforced).
- **Sessions:** 30-min sliding idle timeout; HttpOnly, SameSite=Lax, Secure (HTTPS).

## 4. Authorization
- **API:** `users/permissions.py` — `IsStaff`, `IsStaffOrCreateReadOnly`; `OrderViewSet.get_queryset()` filters to `request.user` for non-staff; `OrderItemViewSet` is staff-only; `perform_create` forces server-side price.
- **Dashboard:** `@login_required` + `@staff_required` (raises 403, audited) / `@user_passes_test(is_staff)`.
- **Products:** `IsAdminOrReadOnly` (public read, staff write).

## 5. Security controls (TLS / headers)
- nginx TLS 1.2/1.3; `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS (configurable), `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=DENY`, referrer policy.
- CSRF middleware enabled; audit middleware records actor/IP/action.

## 6. Security-sensitive entry points (to test live)
- `POST /api/auth/login/` (lockout), `/api/auth/logout/` (blacklist)
- `GET /api/orders/orders/` + `/<id>/` (owner scoping — was H5)
- `POST /api/orders/order-items/` (staff-only, server price — was H6)
- `POST /api/carts/orders/checkout/` (credit+stock+coupon — was H1/H3)
- `POST /dashboard/newsletter/signup/` (coupon generation — was H4)
- `GET /api/docs/` (admin-only now — was H22)
- `GET /admin/users/newslettersubscriber/` (Django admin — access by role)

## 7. Status of my earlier baseline (code review only — NOT yet live-verified)
| ID | Baseline | Code now | Live status |
|---|---|---|---|
| H5 | IDOR orders | Fixed (`orders/views.py:18`) | **RE-TEST** |
| H6 | price/status tamper | Fixed (`orders/serializers.py:10,29`) | RE-TEST |
| H1/H2 | checkout bypass | Fixed (`carts/views.py:106`, `orders/views.py:45`) | RE-TEST |
| H3 | coupon reuse | Fixed (`CouponUsage`) | RE-TEST |
| H4 | predictable coupon | Needs reading `dashboard/views.py` newsletter (reported random in matrix) | RE-TEST |
| H13 | no lockout | Fixed (`audit/backends.py`, throttling) | RE-TEST |
| H19 | JWT after logout | Fixed (blacklist) | RE-TEST |
| H22 | public docs | Fixed (`config/urls.py:22`) | RE-TEST |

> "Fixed in code" ≠ "verified". Each row must be re-tested against the running app and recorded as its own result (DEFENSE HELD / CONFIRMED VULNERABILITY / INCONCLUSIVE). This is a **regression assessment** against the Blue Team's current build, kept separate from the earlier baseline.
