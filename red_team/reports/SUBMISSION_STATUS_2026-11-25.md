# SecureShop — Submission Status, Architecture & Attack/Defense Map

**Date:** 2026-11-25  **Scope:** CET431 SecureShop (Blue Team app) vs Naive Shop (Red Team baseline).
**This file is the single authoritative current-status document.** It is backed by tests that were
actually executed against the running stack on this date; it does not copy older conclusions.

> **One-line verdict:** The application runs end-to-end, every course-topic attack is demonstrated
> to succeed against Naive Shop and to be blocked by SecureShop, the 22-test Django suite passes, and
> all three previously-open findings are re-verified **resolved**. The project is **submission-ready
> for the attack-and-defense scope**; remaining work is documentation polish and (optional) enabling a
> demo MFA account — see §8.

---

## 1. How to run everything

All commands run from the repo root (folder with `docker-compose.yml`).

**Start the stack** (Docker Desktop required):
```powershell
docker compose -f docker-compose.yml -f red_team/docker-compose.override.yml up -d --build --wait
# If host port 80/443 is taken, publish nginx on loopback only (compose override with
#   nginx.ports = ["127.0.0.1:80:80","127.0.0.1:443:443"]) — the app itself is unchanged.
curl.exe -k https://localhost/      # expect 302 -> /dashboard/
```

**Menu runner (one BAT for every test):** `red_team\run_all_tests.bat`
(1 start · 2 live regression · 3 Naive V1–V7 · 4 Bandit/pip-audit · 5 safe suite · 6 final PDF).

**Individual commands:**
```powershell
# Blue-team unit suite (22 tests) — SSL redirect off so the test client isn't 301'd
docker compose -p <project> exec -T -e SECURE_SSL_REDIRECT=False web python manage.py test

# Red-team live regression against SecureShop (property-based; checks real outcomes)
python red_team\live_tests\run_regression.py        # needs the SECURESHOP_* auth env guards

# Naive Shop baseline (two terminals)
python naive_shop\app.py
python red_team\live_tests\attack_naive.py           # V1–V7 -> evidence md

# In-memory verifiers (no Docker needed; need Django on the runner)
python red_team\live_tests\run_safe_tests.py

# Rebuild the single final PDF from current evidence
python red_team\live_tests\generate_final_report.py --replace-existing
```

**Seed accounts:** `admin / Admin!2026#Secure`, `staff / Staff!2026#Secure`,
`customer / Customer!2026#Secure`.

---

## 2. SecureShop architecture (as actually implemented)

```
Browser ──HTTPS 443──▶ nginx (TLS 1.2/1.3 termination; 80 ─301─▶ 443; overwrites X-Forwarded-For)
                          │  HTTP on the internal Docker network (web:8000 not exposed)
                          ▼
                  Gunicorn + Django 5.2 + DRF  (unprivileged UID 1000, WhiteNoise static)
                          │  PostgreSQL protocol
                          ▼
                  PostgreSQL 16        +  Mailpit (local SMTP + web inbox :8025 for confirmations)
```

**Two interfaces over the same models:**
- **Dashboard** (server-rendered templates, Django **session + CSRF**) under `/dashboard/…` — the human UI.
- **REST API** (DRF, **JWT** via SimpleJWT) under `/api/…` — same business logic for clients/tests.

**Middleware order:** `Security → WhiteNoise → Session → CSRF → Auth → AuditMiddleware → Messages → XFrame`.
`AuditMiddleware` records every `403` and exposes the request to model signals (so audit rows know *who*).

### Django apps and responsibilities
| App | Responsibility |
|---|---|
| `users` | `UserProfile` (store_credit, email_confirmed, totp_secret/totp_enabled, last_totp_counter), `Coupon`, `CouponUsage` (single-use constraint), `NewsletterSubscriber`, permission classes, `totp.py`, forms, serializers |
| `products` | `Category`, `Product`; `ProductViewSet` (`IsAdminOrReadOnly`: public read, staff write) |
| `carts` | `Cart`, `CartItem`; add/remove/update-quantity; **atomic `CheckoutView`** (credit + stock + coupon) |
| `orders` | `Order`, `OrderItem`; `OrderViewSet` (owner-scoped `get_queryset`), `OrderItemViewSet` (staff-only), API `CheckoutView` |
| `dashboard` | Session UI: shop, product detail, cart, profile/settings, newsletter, admin pages, 2FA setup/verify, email confirm |
| `audit` | **AAA Accounting**: `AuditLog` model + signals + middleware, `AuthThrottle`, `LockoutModelBackend`, audited JWT login/logout |

### Authentication / authorization / accounting (AAA)
- **AuthN:** `AUTHENTICATION_BACKENDS = [audit.backends.LockoutModelBackend]` refuses to even check the
  password while a username+IP is locked. Dashboard login (`dashboard/views.login_view`) sends
  TOTP-enabled users to `/dashboard/2fa/verify/` before a session is granted. JWT login
  (`audit/views.AuditedTokenObtainPairView` + `TotpTokenObtainPairSerializer`) enforces the TOTP code
  for enrolled users and returns **429** when locked. Passwords: Django **PBKDF2** (1,000,000 iters),
  validators incl. min-length 10. JWT: access 15 min, refresh 1 day, rotate + blacklist-after-rotation;
  logout blacklists the refresh token. Sessions: 30-min sliding idle, HttpOnly/SameSite=Lax/Secure.
- **AuthZ:** `@login_required`+`@staff_required` (raises an audited 403) on dashboard admin pages;
  DRF `IsStaff` / `IsStaffOrCreateReadOnly`; `OrderViewSet.get_queryset` scopes to `request.user`
  for non-staff; order **price is server-side** (serializer `read_only`, `perform_create`).
- **Accounting:** `audit` signals log create/update/delete on tracked models and login/logout/failed-login;
  `AuditLog.record` redacts `password`/`totp_secret` (records *that* they changed, never the value);
  admin is append-only (no add/change/delete).

### Cart / coupon / checkout / order / store-credit flow
1. `add_cart_quantity` (`carts/services.py`) accumulates into the user's `Cart`; rejects when the new
   total would exceed `product.stock` (same cap on the web shop POST, the DRF add, and update-quantity).
2. `CheckoutView` (`carts/views.py`) runs **one `transaction.atomic()`** with `select_for_update()` on
   the cart items, the coupon, and the profile: it recomputes the subtotal from `product.price`
   (never a client value), applies a valid non-expired coupon once (creating a `CouponUsage` row,
   blocked by the unique constraint on reuse), checks store credit and stock, deducts credit,
   decrements stock, creates the `Order`/`OrderItem`s, and clears the cart. Any failure rolls back
   the whole transaction — credit, stock and orders stay consistent.
3. Order history is owner-scoped; staff see all.

---

## 3. Naive Shop architecture (Red Team baseline)

`naive_shop/app.py` — a single-file `http.server` app, **in-memory state**, bound to `127.0.0.1:8010`,
reset by `GET /reset`. It deliberately implements the same seven flaws SecureShop defends against, each
labelled `V1…V7` in the source. It has no database and never handles real payments; it is the
"attack succeeds here" control that the SecureShop defenses are measured against.

---

## 4. Attack → Script → Naive result → SecureShop defense → Evidence

All results below were executed on 2026-11-25 (Naive on loopback; SecureShop on the live Docker/HTTPS stack).

| Course topic | Attack ID | Script | Naive Shop result | SecureShop defense (result) | Evidence |
|---|---|---|---|---|---|
| Lab 1 — client-side price trust | V1 | `attack_naive.py::test_v1`, `run_regression.py::T-H6`, live checkout | Order stored with client price $1.00 (PASS=vuln) | Price read-only + server recompute — client $0.01 → **charged $604.99**; non-staff set price → **403** (HELD) | `evidence/naive_shop/*_all.md`; `evidence/live/regression_*.md` |
| Lab 2.1 — coupon rules | V2 | `attack_naive.py::test_v2`, `verify_inmemory_workflows.py` | Same coupon accepted repeatedly (vuln) | `CouponUsage` unique — 2nd redemption → **400 "already used"**; newsletter codes random `NEWS-<12hex>` (HELD) | `evidence/review/workflow_checks_*.json` |
| Lab 2.2 — exceptional input | — | `verify_inmemory_workflows.py`, live probes | Over-long email truncates to a trusted domain (vuln) | Over-stock/negative/zero/malformed inputs rejected (400); empty body→400, `{}`→400; role never derived from email | `evidence/review/workflow_checks_*.json` |
| Lab 2.3 — workflow validation | V4 | `attack_naive.py::test_v4`, `run_regression.py` | Unpaid order confirmed by replaying a request (vuln) | No separate confirm step; order only created inside the atomic, credit-checked checkout (HELD) | `evidence/live/regression_*.md` |
| Lab 3 — authentication | V5/V6 | `attack_naive.py::test_v5/v6`, `run_regression.py::T-H13/T-H19`, `verify_inmemory_security.py` | Forged identity cookie + no login throttling (vuln) | Server-side identity; lockout **429** after 5 fails; JWT refresh after logout → **401**; TOTP enforced when enabled, single-use (HELD) | `evidence/live/regression_*.md`; `evidence/review/verify_inmemory_security_*.json` |
| Access control / IDOR / RBAC | V3/V7 | `attack_naive.py::test_v3/v7`, `run_regression.py::T-H5/T-H22` | Cross-user order read + unauthenticated admin table (vuln) | Orders owner-scoped → **404** for others; `/api/docs/` and admin → **403** for non-staff (HELD) | `evidence/live/regression_*.md`; `evidence/live/H5_idor_proof.md` |
| Session security | V5 | `run_regression.py::T-H19` | Reusable identity (vuln) | Refresh-token blacklist on logout; Secure/HttpOnly cookies (HELD) | `evidence/live/regression_*.md` |
| Audit / non-repudiation | — | `run_isolated_audit_tests.py` | (not modelled) | Login/logout/denied/CRUD logged; secrets redacted; append-only (HELD) | `evidence/review/audit_tests_*.txt` |
| Misconfiguration | — | `run_regression.py::T-H22`, static scan | — | `DEBUG=False`; docs behind `IsAdminUser`; TLS 1.2/1.3 (HELD) | `evidence/review/bandit_application_*.json` |

Lab 4 (anomaly detection) and Lab 5 (location/time/passkey) are **lecture/lab topics, not SecureShop
features**; the `red_team/labs/` scripts demonstrate the naive-vs-secure idea for each. They are out of
scope for the application per the project's attack-and-defense requirements and were intentionally **not**
added as new app features.

---

## 5. Red Team attack-script inventory

| Script | Purpose |
|---|---|
| `red_team/naive_shop/app.py` (`naive_shop/app.py`) | The intentionally-vulnerable baseline (V1–V7), loopback, in-memory |
| `red_team/live_tests/attack_naive.py` | Runs V1–V7 against Naive Shop; writes sanitized HTTP-exchange evidence |
| `red_team/live_tests/run_naive_suite.py` | Wrapper that starts Naive Shop and runs the suite |
| `red_team/live_tests/run_regression.py` | Property-based live attacks on SecureShop defenses (IDOR, price, lockout, blacklist, docs, cart auth) |
| `red_team/live_tests/run_live_tests.py` | Safe read-only live baseline probes against SecureShop |
| `red_team/live_tests/verify_inmemory_security.py` | Registration/MFA/JWT-TOTP/replay checks on in-memory SQLite |
| `red_team/live_tests/verify_inmemory_totp_ip_lockout.py` | TOTP per-IP lockout on a clean migrated DB |
| `red_team/live_tests/verify_inmemory_workflows.py` | Cart/stock, coupon replay, CSRF, newsletter, checkout integrity |
| `red_team/live_tests/run_isolated_audit_tests.py` | Runs the project's 22 Django tests on in-memory SQLite |
| `red_team/live_tests/run_safe_tests.py` | Runs all non-destructive in-memory + loopback suites |
| `red_team/live_tests/run_static_analysis.py` | Bandit + pip-audit wrapper |
| `red_team/live_tests/generate_final_report.py` | Builds the single final PDF from current evidence (Edge headless) |
| `red_team/labs/lab{1..5}/*.py` | Standalone naive-vs-secure demos for each course lab |

---

## 6. Cart quantity defect — investigated, **not reproducible on the current build**

The previously reported behaviour ("existing 1, requested 3 → 4; cart temporarily exceeds stock") was
re-tested live (throwaway product set to stock=2, throwaway customer) across the web shop POST, the DRF
`cart/add`, and `cart/update-quantity`:

| Scenario | Result |
|---|---|
| Fresh cart, add qty 3 (stock 2) | **Rejected** — cart stays 0 (web `200` no-op / API `400`) |
| Add qty 1 then qty 3 (stock 2) | **Rejected** — cart stays 1 |
| `update-quantity` to 5 (stock 2) | **Rejected 400** — item unchanged at 1 |
| `update-quantity` to 0 / −3 | Item removed (treated as delete) |

"1 + 3 = 4" is **correct add-to-cart accumulation**, not an off-by-one. Over-stock is capped at every
entry point, and checkout re-checks stock atomically. This is covered by the Blue Team's own passing
regression tests `carts/tests.py::CartQuantityTests` (`test_add_uses_requested_quantity_and_rejects_over_stock`,
`test_storefront_add_uses_same_stock_limit`, `test_quantity_update_rejects_stock_excess_without_mutating_item`).
**No code change was made** — changing correct, tested behaviour would risk regressions.
*Residual (optional hardening, not the reported bug):* `add_cart_quantity` is not `select_for_update`-locked,
so under true concurrency two simultaneous adds could transiently overshoot before checkout rejects them.

---

## 7. Previously-reported inconsistencies — resolved & re-verified (2026-11-25)

| Prior claim | Current verified behaviour | Evidence |
|---|---|---|
| Password-only JWT bypasses TOTP for enrolled accounts | **Resolved** — enrolled account, password only → **401** (no token); password + valid code → 200 | live test + `verify_inmemory_security_*.json` (`password_only_access_issued:false`) |
| MFA optional / not enforced | **Enforced when enabled** (enrolment is opt-in); dashboard login redirects to `/dashboard/2fa/verify/` and blocks the shop until verified | live test + `verify_inmemory_security_*.json` |
| `AuthThrottle` migration missing / errors on clean DB | **Present** (`audit/0002`); table exists after a clean migrate; lockout → **429** | live `[401×5, 429, 429]`; `verify_inmemory_totp_ip_lockout_*.json` |
| HTML signup active before email confirmation | **Resolved** — HTML, dashboard and API signup all create an **inactive, unconfirmed** user | `verify_inmemory_security_*.json` (`html_active:false`, `api_active:false`, `dashboard_active:false`) |

---

## 8. Documentation consolidation

- **Authoritative set (kept):** root `README.md` (setup/accounts/architecture), this file, `reports/security_compliance_matrix.md` (topic mapping), `reports/threat_model.md`, `reports/red_team_penetration_test_report.md`, `reports/FINAL_SECURITY_ASSESSMENT_REPORT.pdf` (the **single** final PDF, regenerated 2026-11-25), `docs/TLS_AAA.md`, `red_team/RUN_GUIDE.md`, the `labs/` walkthroughs, and all `secureshop_tests/` test cases.
- **Archived (redundant duplicates, moved — not deleted — to `evidence/naive_shop/_archive/`):** 19 older/duplicate `naive_attack_*` evidence reruns and per-V split files; the latest `naive_attack_20261124T225516Z_all.md` is retained.
- **Evidence preserved:** everything under `evidence/live/`, `evidence/review/`, and the two Naive Shop screenshots. Nothing required for execution, grading, or evidence was removed.
- **Stale status banners corrected:** `red_team/README.md` and `reports/project_architecture.md` now reflect the verified-resolved status instead of the old "open findings" text.

---

## 9. Submission-readiness verdict (vs the official rubric)

| Rubric area | Status | Basis |
|---|---|---|
| Features & functionality (30) | **Ready** | End-to-end: signup→confirm→login/logout, catalogue+search, cart, newsletter+coupon, store-credit checkout+history, profile, admin CRUD. 22 unit tests pass. (Verify mobile viewport + the minor shop JS console item for full polish.) |
| Security coverage (35) | **Ready for the covered topics** | Every course-topic attack: succeeds on Naive, blocked on SecureShop — verified live (§4). Lab 4/Lab 5 are lab topics, not required app features. |
| Security Design Report (10) | **Needs polish** | Threat model + coverage matrix exist; consolidate into one 8–12 page report (this file + the matrix + threat model are the source). |
| Attack evidence & pentest (10) | **Ready** | Fresh V1–V7 + regression evidence + pentest report; final PDF regenerated. Fill any remaining Burp screenshot placeholders for the lab write-ups. |
| Code quality & architecture (5) | **Ready** | Clean app split; runs from the README. |
| Demo & Q&A (10) | **Prepare** | Optionally enable TOTP on a demo staff account to show MFA live; rehearse the §4 attack/defense pairs. |

**Open items (none blocking the attack/defense core):**
1. Consolidate the design report into one 8–12 page document.
2. Confirm every team member has git commits (could not verify — `git` was unavailable on the review shell).
3. Optional: enable TOTP on a demo account; set HSTS > 0 for a production profile; add the DB-backup step (SEC-07).
4. Optional hardening: lock `add_cart_quantity` with `select_for_update` (see §6 residual).
