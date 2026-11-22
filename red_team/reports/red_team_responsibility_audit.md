# CET431 Red Team Responsibility and Completion Audit

**Audit date:** 2026-11-22
**Scope:** Red Team deliverables, Naive Shop status, course-topic coverage, evidence, and remaining submission work.
**Boundary:** Read-only audit. No Blue Team source, database, or existing reports were modified.

## 1. Executive Summary

SecureShop is a Django/PostgreSQL application in the repository root. The Red Team portion is substantially prepared and is separated by the `red_team/` directory, with isolated course labs, live-test scripts, evidence, hypotheses, and generated reports.

The project is **PARTIALLY VERIFIED** overall:

- **Naive Shop:** IMPLEMENTED and 7 attacks have executed successfully in a small local HTTP application.
- **SecureShop live regression:** PARTIALLY VERIFIED. Existing evidence exists for several hypotheses, but reports contain older baseline and final-claim stages that need one final repeatable browser/session pass.
- **Browser evidence:** VERIFIED for signup/login/shop/search/product 404/cart add/checkout/newsletter/order and role-specific Django admin checks.
- **Functional evidence:** PARTIAL; quantity update and account-confirmation behavior have concrete functional findings.
- **Documentation:** PARTIAL; README, threat model, coverage and penetration reports exist, but one complete 8–12 page Security Design Report is not clearly present.
- **Naive/secure comparison:** PARTIAL in completeness but the 7 Naive Shop V1–V7 comparisons have implemented attack evidence.

## 2. Current Project Structure

| Area | Location | Responsibility | Status |
|---|---|---|---|
| SecureShop backend | `/config`, `/users`, `/dashboard`, `/products`, `/carts`, `/orders`, `/audit` | Django application, models, views, forms, RBAC, audit, APIs | VERIFIED |
| SecureShop entry points | `manage.py`, `config/urls.py`, `config/settings.py` | Django startup, routing, database and security configuration | VERIFIED |
| SecureShop infrastructure | `Dockerfile`, `docker-compose.yml`, `nginx/default.conf` | PostgreSQL, Gunicorn, nginx and TLS | VERIFIED |
| Naive Shop | `naive_shop/app.py` | Intentionally vulnerable localhost-only in-memory demo | IMPLEMENTED; browser UI limited |
| Red Team labs | `red_team/labs/lab1_*` through `lab5_*` | In-memory course demonstrations and walkthroughs | IMPLEMENTED |
| Red Team test cases | `red_team/secureshop_tests/` | Endpoint map, hypotheses and test-case definitions | IMPLEMENTED, mostly PARTIALLY VERIFIED |
| Red Team live tools | `red_team/live_tests/` | Naive attacks and SecureShop HTTP/ORM regression | IMPLEMENTED |
| Red Team evidence | `red_team/evidence/` | Browser, live and Naive Shop evidence | PARTIAL |
| Red Team reports | `red_team/reports/` | Coverage, threat, architecture and generated HTML/PDF | PARTIAL |
| Course/Blue documentation | `docs/` | TLS/AAA and attack evidence/pentest notes | PARTIAL |

## 3. Where SecureShop Is

SecureShop is the Django repository root. The application is composed of Django apps:

- `users/`: profiles, coupons, coupon usage, newsletter, signup, permissions and TOTP.
- `products/`: category and product catalogue.
- `carts/`: cart and checkout.
- `orders/`: order and order-item APIs.
- `dashboard/`: server-rendered storefront and staff/admin pages.
- `audit/`: authentication lockout, audit records and middleware.
- `config/`: settings, root routes and WSGI/ASGI.

The live application is served through nginx TLS on `https://localhost`, with Gunicorn on private port 8000 and PostgreSQL 16.

## 4. Naive Shop Status

**Status: IMPLEMENTED and verified through executed script evidence.**

`naive_shop/app.py` is a real local HTTP application using Python's standard library. It listens only on `127.0.0.1:8010` and stores disposable in-memory data. It implements:

- Login and client-controlled identity cookies.
- Product catalogue and `/admin`.
- Checkout and coupon API behavior.
- Order read and confirmation workflow bypass.
- Unprotected administrative UI.

It is not a full UI implementation for the complete catalogue/cart/checkout feature set. It is intentionally a compact lab-specific vulnerable demo.

Evidence:

- `naive_shop/app.py:1-28`
- `naive_shop/app.py:42-65`
- `naive_shop/app.py:91-139`
- `red_team/live_tests/attack_naive.py:1-85`
- `red_team/evidence/naive_shop/attack_results.md`

Naive Shop V1–V7 attack outcomes are all recorded as confirmed:

| Vulnerability | Status |
|---|---|
| V1 client-controlled price | VERIFIED |
| V2 coupon reuse/stacking | VERIFIED |
| V3 order IDOR | VERIFIED |
| V4 workflow bypass | VERIFIED |
| V5 client-controlled identity | VERIFIED |
| V6 no login throttling | VERIFIED |
| V7 open `/admin` | VERIFIED |

No public exposure or Docker isolation is configured for Naive Shop, but binding to loopback and being a standalone process is implemented at `naive_shop/app.py:31-34`.

## 5. Course Vulnerability Coverage

| Topic / lab | Scenario | Naive evidence | SecureShop evidence | Status |
|---|---|---|---|---|
| Lab 1: client trust | Tampered price | V1 | H6 regression/H1 source | PARTIALLY VERIFIED |
| Lab 2.1: coupons | Reuse/stacking | V2 | Existing unique constraint, live browser not final | PARTIALLY VERIFIED |
| Lab 2.2: exceptional input | Negative/invalid quantity | Not implemented by Naive app | Quantity route mismatch found | NOT TESTED/ISSUE FOUND |
| Lab 2.3: workflow | Confirm unpaid | V4 | Checkout browser success, insufficient-credit source | PARTIALLY VERIFIED |
| Lab 3: authentication | Identity/brute force/2FA | V5/V6 | Lockout unit and existing live evidence | PARTIALLY VERIFIED |
| Lab 4: behavioral auth | Z-score/replay | No real Naive app scenario | No implementation found | NOT IMPLEMENTED |
| Lab 5: location/time/passkey/TOTP | MFA and contextual auth | No real Naive app scenario | TOTP groundwork only | PARTIALLY VERIFIED |
| Authorization/IDOR | Other-user order | V3 | Existing owner-scoped code/live evidence | VERIFIED in existing evidence |
| Least privilege | Customer/staff/admin | V7 | Browser: customer denied, staff 403, admin allowed | VERIFIED for newsletter admin |
| Session/JWT replay | Reused refresh token | Not demonstrated separately | Existing JWT blacklist evidence | VERIFIED in existing report |
| TLS/transport | Plaintext/sniffing | Not applicable | HTTPS/browser/admin routes and nginx | VERIFIED |
| SQLi/XSS/CSRF | Injection and forgery | Not part of Naive app | Source claims only | NOT TESTED |

## 6. Verified Red Team Findings

Existing and phase-audit evidence support:

- H4: Newsletter issuance is live-verified as random and duplicate subscriptions do not disclose a second code.
- H5: Existing live evidence verifies owner-scoped order detail/list behavior.
- H9: Existing baseline and current browser evidence show cart quantity route mismatch; the old unauthenticated negative test is not equivalent to browser quantity behavior.
- H13: Automated unit tests cover lockout; live repeated-login evidence is marked inconclusive by the existing regression file.
- H22: Existing browser/API evidence verified non-admin/API-doc restrictions.

Phase-B browser checks added before this audit:

- Disposable registration/login and signed confirmation route.
- Catalogue search and nonexistent-product 404.
- Cart add and database state.
- Cart quantity UI/route mismatch.
- Successful one-item checkout and database order/state update.
- Valid, duplicate and invalid newsletter submissions.
- Live order-history page showing order 18.

## 7. Evidence Status

### What is genuinely present

- 16 Django tests ran and passed.
- Browser screenshots for login/shop/search/404/cart/checkout/newsletter/admin roles.
- Live PostgreSQL backup and database state queries.
- Live Naive Shop attack evidence.
- Bandit and pip-audit evidence.
- HTML/PDF report output.

### What is not sufficiently demonstrated

- Full coupon reuse and coupon application on a completed order.
- Insufficient-credit rejection and repeated checkout.
- Cart remove and clear behavior.
- Profile valid/invalid edit and persistence.
- Desktop/mobile comparison.
- Full admin user/product/coupon create/edit/delete workflows.
- Logout/JWT replay performed from the browser.
- SQLi/XSS/CSRF browser evidence.
- Staff escalation and cross-role operations.
- TOTP/MFA enforcement.
- Behavioral/passkey/location controls.

## 8. Report and Documentation Status

| Deliverable | Status | Finding |
|---|---|---|
| README/setup/test accounts/architecture | IMPLEMENTED | Complete enough to start and understand the project |
| Git history | NOT VERIFIED | Git executable unavailable in the audit shell |
| Threat model | IMPLEMENTED | STRIDE assets, roles and entry points |
| Security Coverage Matrix | PARTIAL | Useful, but contains NOT TESTED rows and older claims |
| Attack Evidence Report | PARTIAL | Many placeholders and mixed baseline/final evidence |
| Red Team Penetration Test Report | PARTIAL | Strong structure, but some final claims exceed current browser evidence |
| Security Design Report 8–12 pages | NOT VERIFIED | No standalone clearly identified report found |
| Demo readiness | IMPLEMENTED at outline level | Rehearsal and missing workflows remain |
| Naive vs SecureShop report | IMPLEMENTED | 7-row comparison with executed evidence |
| HTML/PDF reports | IMPLEMENTED | Existing HTML/PDF set is generated |

## 9. Concrete Misplaced, Duplicate or Inconsistent Items

- **Duplicate security matrices:** `red_team/reports/coverage_matrix.md` and `red_team/reports/security_compliance_matrix.md` overlap.
- **Outdated README:** `red_team/README.md:19-31` states test cases are only prepared later, while live and Naive evidence now exist.
- **Hypothesis file stale:** `red_team/secureshop_tests/hypotheses.md` describes H1/H3/H4/H5/H9/H11/H13/H22 as UNVERIFIED although later evidence exists and code is hardened.
- **Generated HTML/PDF may become stale:** reports must be rebuilt from source after evidence updates.
- **Naive evidence only API-level:** no full browser UI or screenshots; `naive_shop/app.py` is a minimal HTTP UI.
- **Hardcoded demo credentials:** intentionally documented in `README.md`, `users/management/commands/seed_data.py:39-90`, and Naive Shop seed data. They are appropriate for local disposable accounts, but not for production.
- **Default local database password:** `docker-compose.yml:24-28` has `nexus/nexus_password` defaults. Appropriate for local Docker but should not be reused in production.
- **`.env.example` is a development sample:** `DEBUG=True` and placeholder secret at `.env.example:1-2`; production must replace them.
- **Cart route mismatch:** `dashboard/templates/dashboard/cart.html:229` and `:253` use `/api/cart/update-quantity/`; actual route is `/api/carts/cart/update-quantity/` in `carts/urls.py:8-11`. Browser-tested quantity UI changed visually but database quantity did not update.
- **Two signup surfaces:** `/signup/` and dashboard `/dashboard/signup/` need consistent active/confirmation behavior and a final documented workflow.
- **Report claims must be qualified:** HTTP 200/302/403 was used as evidence in some old reports; business/data outcome must remain the deciding signal.

## 10. Recommended Folder Structure

The existing structure is mostly appropriate. The recommended final organization is:

```text
red_team/
├── evidence/
│   ├── live/
│   ├── naive_shop/
│   ├── browser/
│   └── raw/
├── live_tests/
├── labs/
├── secureshop_tests/
├── reports/
│   ├── markdown/
│   ├── html/
│   └── pdf/
└── docs/
```

Avoid duplicating the final coverage matrix in two report names. Keep `coverage_matrix.md` as the canonical coverage source and generated HTML/PDF as derivatives.

## 11. Prioritized Completion Plan

### Critical

1. Finish live end-to-end coupon, checkout, credit and order evidence.
2. Correct or document the cart quantity route mismatch.
3. Clarify account-confirmation behavior and test it consistently.
4. Add actual raw browser/HTTP responses and database deltas to the evidence index.

### High

1. Re-run H4, H5, H13, H22 and H9 safely and independently on the final build.
2. Complete profile, order history, remove/cart clear and admin CRUD browser verification.
3. Replace stale UNVERIFIED hypothesis claims with live statuses.
4. Produce the standalone 8–12 page Security Design Report.
5. Complete mobile and invalid-input tests.

### Medium

1. Generate a final Naive-vs-Secure Shop comparison with screenshots and raw HTTP evidence.
2. Consolidate duplicate matrices and report names.
3. Verify Git commit history and include meaningful-commit evidence.
4. Add a final evidence index and a demo runbook.

## 12. Final Determination

### Already correct

- Red Team assets are separated from Blue Team application code.
- Naive Shop is loopback-local and isolated from SecureShop data.
- Live-test and lab scripts are under `red_team/`.
- Docker/Red Team override changes no Blue Team source file.
- Threat model and test-case folders exist.
- Existing Naive Shop attacks and static-analysis evidence are reproducible.

### Misplaced or duplicated

- Old prepared-status documentation conflicts with actual live evidence.
- Hypotheses remain stale relative to the hardened code.
- Coverage/security matrices overlap.
- Browser evidence is distributed but lacks a complete index.

### Missing

- Final browser end-to-end functional coverage.
- Complete live coupon and checkout business behavior.
- Mobile and profile/admin CRUD evidence.
- A standalone Security Design Report.
- Fresh final-build evidence on all key findings.
- A complete professional evidence appendix.

### Manual verification still required

- Registration and confirmation enforcement.
- Cart add/remove/clear/quantity and session persistence.
- Coupon application and reuse.
- Store-credit checkout and confirmation.
- Profile editing.
- Desktop/mobile usability.
- Admin user/product/coupon CRUD.
- Logout and H13/H22/H5/H9 browser/API retests.
- Git history and security-design report quality.
