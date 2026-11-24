# SecureShop — Attack Evidence Report

**Date:** 2026-11-25 · **Rule:** a `200`/`403` status is never the finding by itself — each case is judged
on the **actual outcome** (stored data, DB state, ownership). Naive Shop is `http://127.0.0.1:8010`
(baseline); SecureShop is the live `https://localhost` Docker/HTTPS/PostgreSQL stack.

| # | Attack | Naive Shop | SecureShop | Evidence |
|---|---|---|---|---|
| V1 | Client price tamper | VULNERABLE | **BLOCKED** | below + `evidence/live/regression_*.md` |
| V2 | Coupon reuse | VULNERABLE | **BLOCKED** | below + `evidence/review/workflow_checks_*.json` |
| V3 | IDOR (other's order) | VULNERABLE | **BLOCKED** | `evidence/live/H5_idor_proof.md` |
| V4 | Workflow / unpaid confirm | VULNERABLE | **BLOCKED** | below |
| V5 | Forged identity cookie | VULNERABLE | **BLOCKED** | `evidence/review/verify_inmemory_workflows_*.json` |
| V6 | No login throttling | VULNERABLE | **BLOCKED** | below |
| V7 | Unauthenticated admin | VULNERABLE | **BLOCKED** | below + `evidence/naive_shop/*.png` |
| A1 | Password-only JWT (TOTP on) | n/a | **BLOCKED** | `evidence/review/verify_inmemory_security_*.json` |
| A2 | Refresh replay after logout | n/a | **BLOCKED** | `evidence/live/regression_*.md` |

---

### V1 — Excessive client-side trust (price tamper)
- **Attack:** `POST /api/carts/orders/checkout/` (SecureShop) / `POST /api/checkout {"product_id":1,"price":1}` (Naive), sending a tiny client price for a high-priced item.
- **Naive:** order persisted with `total = $1.00` for the $1,337 jacket → **VULNERABLE**.
- **SecureShop:** the client price is ignored; the server recomputed the real total. Sending `price/total/subtotal = 0.01` for the $599.99 item, the server **charged $604.99** (599.99 + $5 shipping) and deducted it from store credit. Non-staff `POST /api/orders/order-items/ {price:0.01}` → **403**. → **BLOCKED**.

### V2 — Flawed business rules (coupon reuse)
- **Attack:** apply the same coupon to a second order (`{"coupon_code":"SUMMER2026"}`).
- **Naive:** `/api/apply_coupon` returns the discount every time → **VULNERABLE**.
- **SecureShop:** first redemption `200`; second redemption → **`400 {"error":"Coupon has already been used."}`** (enforced by the `CouponUsage (user,coupon)` unique constraint). Newsletter coupons are random `NEWS-<12 hex>`, unique per request. → **BLOCKED**.

### V3 — IDOR (read another user's order)
- **Attack:** authenticated customer requests `GET /api/orders/orders/3/` (an order owned by user id 3).
- **Naive:** `GET /api/orders/{id}` returns any order regardless of owner (Bob read Alice's order) → **VULNERABLE**.
- **SecureShop:** `get_queryset` is scoped to `request.user`, so a non-owner request → **404**; the list endpoint returns only the caller's own orders. → **BLOCKED** (`evidence/live/H5_idor_proof.md`).

### V4 — Insufficient workflow validation (pay-less / replay confirm)
- **Attack:** reach order "confirmed" without a successful, credit-checked payment.
- **Naive:** `GET /orders/confirm?order=N` (or `/api/confirm`) flips an unpaid order to paid → **VULNERABLE**.
- **SecureShop:** there is **no standalone confirm endpoint**; an `Order` is created only inside the atomic `CheckoutView`, which requires sufficient store credit and stock and records a `CouponUsage`. Skipping/replaying steps cannot produce a paid order. → **BLOCKED**.

### V5 — Client-controlled identity cookie
- **Attack:** send `Cookie: user=admin` and act as that user.
- **Naive:** the app trusts the `user` cookie as identity → **VULNERABLE**.
- **SecureShop:** identity is the Django session subject / JWT subject; a forged `user=admin` cookie does **not** authenticate (`/dashboard/profile/` → 302 to login, `user.is_authenticated == False`). → **BLOCKED**.

### V6 — Missing login throttling (brute force)
- **Attack:** repeated failed logins, then a valid one / code spraying.
- **Naive:** eight wrong passwords then a correct login all succeed, no lockout → **VULNERABLE**.
- **SecureShop:** `LockoutModelBackend` + `AuthThrottle` lock the username+IP. Live: 7 failed `POST /api/auth/login/` returned **`[401,401,401,401,401,429,429]`** — locked after 5. Per-IP TOTP lockout at 20. → **BLOCKED**.

### V7 — Unauthenticated admin / RBAC
- **Attack:** fetch an admin/users view with no authentication.
- **Naive:** `GET /admin` returns every user, role and credit to anonymous (screenshot `evidence/naive_shop/naive-shop-admin.png`) → **VULNERABLE**.
- **SecureShop:** `/admin/*` and staff dashboard pages require auth + staff; non-staff → audited **403**; `/api/docs/` (Swagger) → **403** for non-admin. → **BLOCKED**.

### A1 — Password-only JWT for a TOTP-enabled account
- **Attack:** `POST /api/auth/login/ {username,password}` (no code) for an enrolled account.
- **SecureShop:** → **401** (no token). With a valid 6-digit code → 200. Codes are single-use (`last_totp_counter`); replay → 401. → **BLOCKED**.

### A2 — Refresh-token replay after logout
- **Attack:** logout, then reuse the old refresh token at `/api/auth/refresh/`.
- **SecureShop:** logout blacklists the refresh token; reuse → **401**. → **BLOCKED**.

---

**Reproduce:** `red_team\run_all_tests.bat` (option 3 Naive, option 2 live regression, option 5 safe suite),
or the individual commands in `SUBMISSION_STATUS_2026-11-25.md` §1. Raw transcripts are under
`red_team/evidence/` (`naive_shop/`, `live/`, `review/`).
