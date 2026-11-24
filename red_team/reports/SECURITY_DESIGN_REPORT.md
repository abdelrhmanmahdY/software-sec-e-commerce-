# SecureShop — Security Design Report

**Course:** CET431 Software Security (Fall 2026) · **Project:** SecureShop e-commerce · **Date:** 2026-11-25
**Scope:** This report satisfies the rubric's "Security Design Report (8–12 pages): threat model (assets,
entry points, attackers) and the complete Security Coverage Matrix." All defense claims are backed by
tests executed against the running application on this date (see §6 and the Attack Evidence Report).

---

## 1. Introduction

SecureShop is a Django 5.2 + DRF e-commerce application hardened against the business-logic and
authentication attacks taught in CET431. The Red Team demonstrates each attack against an intentionally
vulnerable baseline (**Naive Shop**, `naive_shop/app.py`) and verifies that the equivalent attack is
blocked by SecureShop. This document describes the assets to protect, the attack surface, the threats
(STRIDE), and a complete per-topic coverage matrix mapping each course topic to the attack scenario, its
root cause, the implemented defense, the exact code location, and the evidence.

## 2. System overview (security-relevant)

```
Browser ──HTTPS 443──▶ nginx (TLS 1.2/1.3; 80→301→443; overwrites X-Forwarded-For)
                          │ internal HTTP (web:8000 not exposed)
                          ▼
                  Gunicorn + Django + DRF  ──▶  PostgreSQL 16   (+ Mailpit for confirmation email)
```

- **Two interfaces, one set of models:** server-rendered **dashboard** (`/dashboard/…`, session + CSRF)
  and a **REST API** (`/api/…`, JWT). Both enforce the same server-side rules.
- **AAA** lives in the `audit` app (accounting), `audit/backends.py` + `users/totp.py` (authentication),
  and `users/permissions.py` + viewset scoping (authorization).
- Full architecture: see `SUBMISSION_STATUS_2026-11-25.md` §2.

## 3. Threat model

### 3.1 Assets
| Asset | Why it matters |
|---|---|
| Credentials & password hashes (`auth_user`) | Account takeover; offline cracking if leaked |
| Store credit (`users_userprofile.store_credit`) | Directly spendable value |
| Orders / order history (`orders_order`) | Confidentiality (IDOR) + integrity |
| Product pricing (`products_product`) | Revenue integrity (price tampering) |
| Coupons (`users_coupon`, `users_couponusage`) | Discount-abuse / infinite-money |
| Admin control plane (Django admin, staff dashboard) | Full compromise if reachable |
| Audit log (`audit_auditlog`) | Non-repudiation; must be tamper-evident |

### 3.2 Actors / attackers
- **Anonymous visitor** — browse, register, log in.
- **Customer** — owns a cart, spends store credit, manages own profile.
- **Staff** — manages products/users/orders.
- **Admin (superuser)** — full Django admin.
- **Attacker variants** — unauthenticated, authenticated customer abusing their own session, and a
  malicious insider (staff). Capabilities assumed: can craft arbitrary HTTP requests (Burp), edit cookies
  and JSON bodies, replay captured requests, and brute-force codes.

### 3.3 Entry points (attack surface)
`/dashboard/signup|login|2fa/verify|shop|cart|newsletter/signup|settings`,
`/api/auth/login|logout|refresh`, `/api/orders/orders|order-items|checkout`,
`/api/carts/cart/add|update-quantity|checkout`, `/api/products/*`, `/api/docs/`, `/admin/*`.
Every form field, URL parameter and JSON key on these is treated as untrusted.

### 3.4 Trust boundaries
1. Browser ↔ nginx (TLS termination). 2. nginx ↔ Django (private network; X-Forwarded-For overwritten).
3. Django ↔ PostgreSQL. 4. **Identity/price boundary** — the client is never trusted for identity,
price, role, or payment state; the server recomputes all of them.

### 3.5 STRIDE summary
See `threat_model.md` for the full STRIDE table (all elements **Mitigated**, verified live 2026-11-25):
Spoofing (lockout + TOTP), Tampering (server-side price, owner scoping), Repudiation (audit log),
Information disclosure (TLS, RBAC on docs/admin), Denial of service (throttling, atomic checkout),
Elevation of privilege (staff-only permissions).

## 4. Security Coverage Matrix (complete)

One row per course topic: the attack scenario in SecureShop, the root cause it addresses, the defense
implemented, where it lives in the code, and the evidence. Status is **DEFENSE HELD** unless noted.

| # | Course topic | Attack scenario (SecureShop) | Root cause addressed | Defense implemented | Code location | Evidence | Status |
|---|---|---|---|---|---|---|---|
| 1 | Excessive client-side trust (Lab 1) | Submit a low `price`/`total` at checkout or on an order item | Server trusting client-sent price | Order price is `read_only`; checkout recomputes subtotal from `product.price`; `perform_create` forces price | `orders/serializers.py:10,33`; `carts/views.py:124` | Live: client $0.01 → charged $604.99; non-staff set price → 403. `evidence/live/regression_*.md` | HELD |
| 2 | Flawed business rules — coupons (Lab 2.1) | Reuse / stack / alternate coupon codes | No per-user single-use tracking | `CouponUsage` unique constraint `(user, coupon)`; one `select_for_update` coupon per checkout | `users/models.py:34-43`; `carts/views.py:127-156` | Live: 2nd redemption → 400 "already used". `evidence/review/workflow_checks_*.json` | HELD |
| 3 | Inconsistent handling of exceptional input (Lab 2.2) | Over-long email / negative / huge / malformed quantity & ids | Divergent validation; silent truncation | Integer/stock validation on every cart path; `EmailField`; roles never derived from email domain; generic 400s | `carts/views.py:38-98`; `carts/services.py`; `dashboard/views.py:600-619` | In-memory + live probes: over-stock/negative/empty → 400. `evidence/review/workflow_checks_*.json` | HELD |
| 4 | Insufficient workflow validation (Lab 2.3) | Reach "order confirmed" without paying / replay confirm | No server-side state machine / payment check | Order is created only **inside** the atomic, credit-and-stock-checked checkout; no standalone confirm endpoint | `carts/views.py:103-180`; `orders/views.py:35-79` | Live regression + checkout invariants. `evidence/live/regression_*.md` | HELD |
| 5 | Authentication — identity forgery (Lab 3) | Forge a `user`/`verify` cookie to become another user | Client-controlled identity | Identity is the Django session / JWT subject; forged `user=admin` cookie does not authenticate | `audit/backends.py`; Django session middleware | In-memory forged-cookie test → not authenticated (302). `evidence/review/verify_inmemory_workflows_*.json` | HELD |
| 6 | Authentication — brute force (Lab 3) | Spray passwords / codes | No lockout or throttling | `LockoutModelBackend` (user+IP, 429), DRF throttling, per-IP TOTP lockout, `AuthThrottle` table | `audit/backends.py`; `audit/utils.py`; `config/settings.py:159,170` | Live: `[401×5,429,429]`; `evidence/review/totp_ip_lockout_*.json` | HELD |
| 7 | 2FA / TOTP (Lab 5 time-based) | Password-only token for a TOTP-enabled account; replay a code | MFA not enforced / codes reusable | TOTP enforced on JWT and dashboard login when enabled; single-use via `last_totp_counter` | `audit/views.py:26-67`; `dashboard/views.py:129-217`; `users/totp.py:122-174` | Live: password-only → 401; valid code → 200. `evidence/review/verify_inmemory_security_*.json` | HELD |
| 8 | Access control / IDOR / RBAC | Read/modify another user's order; non-staff admin actions | Missing object/role checks | `OrderViewSet.get_queryset` owner scope; `IsStaff`/`IsStaffOrCreateReadOnly`; `@staff_required` (audited 403) | `orders/views.py:18-21`; `users/permissions.py`; `dashboard/views.py:38` | Live: `/orders/3/` → 404; non-staff admin → 403. `evidence/live/H5_idor_proof.md` | HELD |
| 9 | Session security (Lec 5) | Replay a refresh token after logout | No token invalidation | Refresh-token blacklist on logout; rotate+blacklist-after-rotation; Secure/HttpOnly/SameSite cookies | `audit/views.py:90-100`; `config/settings.py:141-184` | Live: reused refresh → 401. `evidence/live/regression_*.md` | HELD |
| 10 | Password storage (Lec 4) | Offline cracking if the hash DB leaks | Fast/unsalted hashing | Django **PBKDF2** (1,000,000 iters) + per-user salt; validators (min 10, common, numeric) | `config/settings.py:161-167`; verified in DB (`pbkdf2_sha256$1000000$`) | DB hash prefix inspected; unit tests. | HELD |
| 11 | Accounting / non-repudiation (Lec 1-2) | Deny an action; tamper with the log | No audit trail | `AuditLog` on login/logout/denied/CRUD with actor+IP+old→new; secrets redacted; admin append-only | `audit/models.py`; `audit/signals.py`; `audit/admin.py` | Unit tests + live audit stream. `evidence/review/audit_tests_*.txt` | HELD |
| 12 | Misconfiguration / exposure | Reach API schema or run with DEBUG | Permissive config | `DEBUG=False`; Swagger `public=False` + `IsAdminUser`; `ALLOWED_HOSTS`; security headers | `config/urls.py:28-39`; `config/settings.py:138-154` | Live: unauth `/api/docs/` → 403. `evidence/live/regression_*.md` | HELD |
| 13 | Transport security / TLS (Lec 5) | Downgrade / sniff traffic | Plain HTTP | nginx TLS 1.2/1.3, forward-secret ciphers; 80→301→443; Secure cookies; proxy-aware redirect | `nginx/default.conf`; `config/settings.py:138-154` | TLS termination verified; `docs/TLS_AAA.md`. (HSTS=0 — raise for prod.) | HELD* |
| 14 | SQL injection (optional) | Injection via search / ids | String-built SQL | Django ORM parameterization everywhere; no raw SQL on untrusted input | all views (ORM) | Probes returned no injection; ORM by design. | HELD |
| 15 | XSS (optional) | Stored/reflected script in product/search | Unescaped output | Template auto-escaping; JSON APIs; `textContent` in JS | `dashboard/templates/*` | No reflected execution observed. | HELD |
| 16 | CSRF | Cross-site state change on dashboard | Missing CSRF protection | `CsrfViewMiddleware`; `CSRF_COOKIE_SECURE`; SameSite=Lax | `config/settings.py:73,142,154` | In-memory: POST without token → 403. `evidence/review/verify_inmemory_workflows_*.json` | HELD |
| 17 | Registration / email confirmation | Use an account before confirming email | Active-before-confirm | Signup creates `is_active=False`; signed confirmation token (3-day TTL) activates | `users/registration.py`; `dashboard/views.py:631-644` | In-memory: html/api/dashboard signup all inactive. `evidence/review/verify_inmemory_security_*.json` | HELD |
| 18 | Dependency vulnerabilities (SCA) | Exploit an outdated package | Unpatched deps | `pip-audit` in the test runner; pinned `requirements.txt` | `red_team/live_tests/run_static_analysis.py` | `evidence/review/pip_audit_*.json` — re-run & patch before submission | TRACK |
| 19 | Anomaly detection (Lab 4) | — | — | Lecture/lab topic; demonstrated as a standalone naive-vs-secure demo, **not** a SecureShop feature | `red_team/labs/lab4_anomaly_detection/` | `labs/.../walkthrough.md` | N/A (lab topic) |
| 20 | Location / passkey (Lab 5) | — | — | Lecture/lab topic; TOTP (time-based) is the implemented factor; location/passkey are demos only | `red_team/labs/lab5_location_time_passkey/` | `labs/.../walkthrough.md` | N/A (lab topic) |

\* HELD with a production note: enable HSTS (`SECURE_HSTS_SECONDS` > 0) when deploying under a real certificate.

## 5. Defense-in-depth & secure-design principles applied
- **Least privilege:** customers see only their own orders; staff-only mutations; append-only audit.
- **Complete mediation:** every sensitive route re-checks identity, ownership, price and stock server-side.
- **Fail securely:** checkout is one atomic transaction — any failure rolls back credit, stock and orders.
- **Economy/open design:** standard Django/DRF controls, no custom crypto or hidden-page "security".
- **Separation of duties:** AAA split across `audit` (accounting), backends/TOTP (authN), permissions (authZ).

## 6. Assurance & testing summary
- **22/22** Django unit tests pass (`manage.py test`, SSL-redirect off for the test client).
- **Live regression** (`run_regression.py`) against Docker/HTTPS/PostgreSQL: every row DEFENSE HELD.
- **Naive Shop V1–V7** reproduce on loopback (the baseline the defenses are measured against).
- **In-memory verifiers** confirm MFA enforcement, lockout on a clean DB, coupon replay rejection, CSRF, and signup inactivity.
- Full method and commands: `SUBMISSION_STATUS_2026-11-25.md` §1; evidence under `red_team/evidence/`.

## 7. Residual risks (non-blocking)
MFA enrolment is opt-in (enforced when enabled); `add_cart_quantity` is not row-locked (checkout is the
atomic gate); HSTS is 0; DB backups (SEC-07) not automated; re-run `pip-audit` and patch before submission.
None affects the attack-and-defense core, which is fully verified above.
