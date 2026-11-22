# Naive Shop vs SecureShop — Comparison

The required naive-vs-secure comparison. Each row is the **same attack idea** run against two apps:
- **Naive Shop** (`naive_shop/`, `http://127.0.0.1:8010`) — intentionally insecure; attacks **succeed** (see `evidence/naive_shop/attack_results.md`).
- **SecureShop** (current hardened build, `https://localhost`) — attacks **blocked** (see `evidence/live/regression_results.md`).

All results are from **real executed tests**, not assumptions.

| # | Course topic | Attack | Naive Shop result | SecureShop result | Why SecureShop wins |
|---|---|---|---|---|---|
| 1 | Client-side trust (Lab 1) | Send a low `price` at checkout | **CONFIRMED** — charged $1 for the $1337 jacket | **DEFENSE HELD** — customer `POST order-items price=0.01` → 403; price is server-side & read-only | Server never trusts a client price (`orders/serializers.py:10`, `orders/views.py:32`) |
| 2 | Business rules (Lab 2.1) | Apply a coupon twice | **CONFIRMED** — `SAVE20` accepted twice | **DEFENSE HELD** — second use blocked by unique `(user,coupon)` | `CouponUsage` constraint (`users/models.py:28`) |
| 3 | Access control / IDOR | Read another user's order | **CONFIRMED** — bob fetched alice's order (HTTP 200) | **DEFENSE HELD** — customer `GET /orders/3/` (not owner) → 404 | `get_queryset` owner scoping (`orders/views.py:18`) |
| 4 | Workflow validation (Lab 2.3) | Confirm an order without paying | **CONFIRMED** — order marked `paid=true` with no payment | **DEFENSE HELD** — checkout requires store credit ≥ total, atomic | `transaction.atomic` + `select_for_update` (`carts/views.py:106`) |
| 5 | Authentication (Lab 3) | Forge identity via a client value | **CONFIRMED** — `user` cookie trusted unchanged | **DEFENSE HELD** — identity from server session/JWT; forged refresh after logout → 401 | Server-side identity + JWT blacklist (`audit/views.py:34`) |
| 6 | Brute-force protection | Many failed logins | **CONFIRMED** — 8 bad logins, never locked | **DEFENSE HELD** — lockout returns 429 after 5 | `LockoutModelBackend` + throttling (`config/settings.py:159`) |
| 7 | Least Privilege / AuthZ | Reach admin with no rights | **CONFIRMED** — `/admin` open to anyone | **DEFENSE HELD** — `/admin/...` → login; `/api/docs/` → 403 | `IsStaff`/`IsAdminUser`, admin gate (`users/permissions.py`, `config/urls.py:22`) |

## Reading the comparison
The Naive Shop is the "attack works against a naive implementation" half required by the project (PDF item 3). SecureShop is the "and fails against their own" half. Both halves are backed by executed evidence files, kept separate from the educational Python demos in `labs/`.

## How to reproduce
```
# naive (vulnerable)
python naive_shop/app.py            # then:
python red_team/live_tests/attack_naive.py

# secure (defended) — app must be running via Docker
python red_team/live_tests/run_regression.py
```
