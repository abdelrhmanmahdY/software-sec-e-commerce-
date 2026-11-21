# SecureShop — Live Baseline Report (Initial)

**Date:** 2026-11-21 · **Target:** `http://127.0.0.1:8000` (local Docker, authorized baseline) · **Tester:** Red Team (sole member).

> This is an **INITIAL BASELINE** against an **unfinished** Blue Team app. It is **not** the final finding set. When the Blue Team ships the final version, re-run and record **Regression Results** separately (keep each version apart).

## Three result types — kept separate (project requirement F)

1. **Isolated Python Demo** — proves the teaching example works (`labs/`). *Not* evidence about SecureShop.
2. **Source Code Review** — suspicion points from reading the code (`secureshop_tests/hypotheses.md`). *Not* a confirmed vulnerability.
3. **Live SecureShop Test** — the real test below. Only these results carry `CONFIRMED VULNERABILITY` / `TESTED - NOT VULNERABLE`.

---

## 1. Did SecureShop run? — YES
- Ran via Docker (`run_secureshop_docker.bat` → `docker compose up --build`). PostgreSQL + Django (5.2.4) started; migrations applied; `seed_data` run.
- App reachable at `http://127.0.0.1:8000/` (HTTP 200). Test accounts created: `admin`, `staff`, `customer`.

## 2. Functions exercised (live)
- Server home (`GET /`) → 200.
- JWT auth (`POST /api/auth/login/` as customer) → token issued.
- Product list (`GET /api/products/products/`) → 200.
- Orders API (`GET /api/orders/orders/`) → 200.
- Cart update endpoint (`POST /api/carts/cart/update-quantity/`) → 403 without auth.
- Newsletter signup (`POST /dashboard/newsletter/signup/`) → coupon issued.
- (Registration/checkout UI flows: not fully driven in this automated baseline — see "Not tested".)

## 3. Live test results

| Test | Hyp | Status | Evidence / detail |
|---|---|---|---|
| T-UP server reachable | — | TESTED - NOT VULNERABLE | `GET /` → 200 |
| T-AUTH JWT login | — | TESTED - NOT VULNERABLE | token issued |
| **T-SWAGGER** API docs public | H22 | **CONFIRMED VULNERABILITY** | `GET /api/docs/` (no auth) → 200 |
| T-UPDQTY-NOAUTH auth required | H9 | TESTED - NOT VULNERABLE | no-auth POST → 403 |
| T-ERRLEAK error body | H8 | INCONCLUSIVE | unauth gave a 403 HTML page, not a JSON error; needs an authenticated malformed request (session+CSRF) to judge |
| T-PROD-READ product list | — | TESTED - NOT VULNERABLE | 200 (public read is by design) |
| **T-ORDERS-IDOR** cross-user order read | H5 | **CONFIRMED VULNERABILITY** | customer (id 3) read admin's order (id 2, user 1); staff (id 2) read customer's order. See `evidence/live/H5_idor_proof.md` |
| **T-RATELIMIT** login lockout | H13 | **CONFIRMED VULNERABILITY** | 6 wrong logins → `[401×6]`, no lockout/throttle |
| **T-NEWSLETTER** predictable coupon | H4 | **CONFIRMED VULNERABILITY** | issued `NEWS0003` (pattern `NEWS####`, and same code reissued) |

## 4. Attacks that SUCCEEDED (live, this baseline)
- **H5 — Broken Access Control (IDOR):** any authenticated user reads all orders. (`orders/views.py:9-17`)
- **H13 — No login rate limiting / lockout:** brute force unthrottled. (`settings.py`, no throttle)
- **H4 — Predictable newsletter coupon codes:** `NEWS####` guessable, not unique. (`dashboard/views.py:445-448`)
- **H22 — API schema exposed without auth:** `/api/docs/` public. (`config/urls.py:42-43`)

## 5. Attacks that FAILED because a defense held (live)
- **H9 — update-quantity without auth:** returned 403 (not reachable unauthenticated) → control present.
- Product read requires nothing by design (not a failure, expected public read).

## 6. Not tested / blocked (and why)
- **H1, H2, H3, H6, H16 (T-CHECKOUT-PAY, T-CHECKOUT-FREE, T-COUPON-REUSE, T-PRICE-TAMPER, T-STAFF-ESC):** `NOT TESTED` — they change important data, spend store credit, or are destructive. Run manually on a recoverable DB during the agreed window using `secureshop_tests/test_cases/`.
- **H8 error leakage:** `INCONCLUSIVE` — needs an authenticated session + CSRF to hit the JSON error path.
- **Registration/login UI, confirmation (H11, H12, H14), JWT-after-logout (H19), password storage (H20):** `NOT TESTED` in this automated pass; prepared as manual steps.

## 7. What the Blue Team needs to fix (from live baseline)
| Priority | Fix |
|---|---|
| High | Scope Orders API to the owner (`get_queryset` filter + object permissions) — H5 |
| High | Add login rate limiting / lockout (DRF throttling or django-axes) — H13 |
| Medium | Make coupon codes random + single-use + unique — H4 |
| Medium | Restrict `/api/docs/` to staff or disable in production — H22 |

## 8. What must be re-tested after Blue Team changes (regression)
All rows above, plus the `NOT TESTED` items, re-run against the final version; record as a **separate** regression report. Keep this baseline for comparison.

---

### How this was produced (reproducible)
1. `docker compose up --build -d` then `docker compose exec web python manage.py seed_data`.
2. `python red_team/live_tests/run_live_tests.py` → `evidence/live/baseline_results.md`.
3. H5 cross-user proof: see `evidence/live/H5_idor_proof.md`.
