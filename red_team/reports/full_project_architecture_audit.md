# Full Project Structure, Architecture, Integration, and Code Quality Audit

**Audit date:** 2026-11-22
**Scope:** Repository structure, architecture, infrastructure, integration, code quality and Blue/Red separation.
**Boundary:** Audit only. No files, source code, database records or configuration were modified.

## 1. Executive Summary

The repository is a Django monolith with clear app-level separation and a separate Red Team workspace. Infrastructure is centered on Docker Compose, PostgreSQL, Gunicorn and nginx TLS.

Primary findings:

- **VERIFIED:** Django app boundaries, Docker services, PostgreSQL connectivity and TLS termination.
- **VERIFIED:** Red Team tools are separate from Blue Team runtime code.
- **ISSUE FOUND:** `/api/cart/update-quantity/` in `dashboard/templates/dashboard/cart.html:229,253` does not match the actual `/api/carts/cart/update-quantity/` route.
- **ISSUE FOUND:** browser quantity UI changed without a database quantity update.
- **ISSUE FOUND:** account confirmation is provided, but live signup created an active account and login succeeded before confirmation state was changed.
- **PARTIALLY VERIFIED:** test suite, live evidence and report claims are mixed across baseline, current, final and template states.
- **ISSUE FOUND:** some documentation and hypothesis files are stale.

## 2. Repository Structure Map

| Path | Purpose | Assessment |
|---|---|---|
| `config/` | Django settings, root URLs, WSGI/ASGI | Correct |
| `users/` | Account/profile, coupons, newsletter, permissions | Correct |
| `dashboard/` | Server-rendered UI, staff/customer workflows | Correct, with integration defects |
| `products/` | Category/product catalogue and API | Correct |
| `carts/` | Cart and checkout API/web logic | Correct but route mismatch |
| `orders/` | Order and order-item API | Correct owner-scoping in current code |
| `audit/` | Lockout, accounting and JWT logout support | Correct and isolated |
| `naive_shop/` | Intentionally vulnerable local demo | Correct separation, but limited UI |
| `red_team/labs/` | Course lab demonstrations | Correct |
| `red_team/live_tests/` | Executed HTTP/Naive/SecureShop checks | Correct |
| `red_team/secureshop_tests/` | Hypotheses and test-case definitions | Appropriate but stale statuses |
| `red_team/evidence/` | Screenshots, logs and database evidence | Needs stronger index |
| `red_team/reports/` | Markdown/HTML/PDF reports | Appropriate |
| `docs/` | Architecture/attack documentation | Appropriate |
| `nginx/` | TLS/proxy configuration | Correct |
| `certs/` | Local certificates | Correct for local demo, production key replacement needed |

## 3. Blue Team / Red Team Separation

**VERIFIED:** `red_team/` contains testing, evidence and reporting assets, while `naive_shop/` is outside the Django apps. The Red Team Docker override is intended to avoid edits to Blue Team scripts:

- `red_team/docker-compose.override.yml:1-14`
- `red_team/docker-compose.override.yml:19-52`

**VERIFIED:** Naive Shop binds to loopback only:

- `naive_shop/app.py:31-34`
- `naive_shop/app.py:1-28`

**ISSUE FOUND:** test credentials are intentionally present in README and seed code. They are suitable for local demo but must not be reused in production:

- `README.md`
- `users/management/commands/seed_data.py:39-90`

**PARTIALLY VERIFIED:** Red Team scripts are separated, but report claims and current live evidence are not always synchronized.

## 4. Architecture Assessment

### App responsibilities

**VERIFIED:** app names map to clear ecommerce/audit responsibilities.

- `users/models.py`: profiles, coupons and newsletter.
- `orders/models.py`: order and order items.
- `carts/models.py`: cart and item ownership.
- `products/models.py`: catalogue.
- `dashboard/views.py`: presentation workflows.
- `audit/`: lockout and accounting.

### Views/models/forms/routes/permissions

- Django models and forms exist in conventional locations.
- Dashboard views mix presentation and business logic, for example checkout logic in `carts/views.py:79-157` and dashboard checkout UI in `dashboard/templates/dashboard/cart.html:324-363`.
- Shared authorization helpers are centralized in `users/permissions.py:1-31`.
- Owner scoping is implemented in `orders/views.py:12-19`.
- The schema view is restricted to admin users in `config/urls.py:12-25`.

**PARTIALLY VERIFIED:** coupling is acceptable for a course monolith, but route names and URL prefixes can be confusing.

## 5. Network and Infrastructure

**VERIFIED:**

- Docker Compose defines PostgreSQL, web and nginx.
- PostgreSQL is isolated from the host by default; the Red Team override removes the host binding.
- The web container is exposed only internally.
- nginx redirects HTTP to HTTPS and proxies to `web:8000`.
- TLS 1.2/1.3 is selected in nginx.
- Gunicorn runs as an unprivileged UID in `Dockerfile:20-22`.

Key locations:

- `docker-compose.yml:20-32`
- `docker-compose.yml:37-74`
- `docker-compose.yml:77-91`
- `Dockerfile:1-24`
- `nginx/default.conf:5-45`

### Security headers and proxy

- `nginx/default.conf:13-34`: TLS protocols/ciphers and server token setting.
- `nginx/default.conf:38-45`: forwarded protocol and controlled forwarded IP.
- `config/settings.py:133-151`: HTTPS and secure cookie settings.
- `config/settings.py:153-168`: session and auth lockout settings.

**ISSUE FOUND:** local `.env.example:1-2` has `DEBUG=True` and a placeholder secret, which is unsuitable if copied to a production environment.

**PARTIALLY VERIFIED:** HSTS is controlled and can be raised for production, but the local default is not final production evidence.

## 6. Security Architecture

**VERIFIED:**

- Session and JWT authentication.
- Owner-based order queryset.
- Staff/admin permission checks.
- Atomic checkout and stock/credit checks.
- CSRF middleware and secure cookies.
- Audit middleware/signals.
- Newsletter duplicate and coupon usage controls.

Key locations:

- `orders/views.py:12-19`
- `carts/views.py:79-157`
- `users/permissions.py:6-31`
- `config/settings.py:153-178`
- `audit/`
- `users/models.py:26-37`

**ISSUE FOUND:** TOTP fields/routes exist, but seed accounts do not enforce MFA. `dashboard/views.py:110-160` and `users/models.py:1-12`.

**NOT VERIFIED:** Behavioral anomaly detection, passkey, impossible-travel and replay-resistant location controls are absent or not applicable.

## 7. Code Quality and Duplication

### Findings

1. **ISSUE FOUND — Cart URL mismatch**
   - Frontend: `dashboard/templates/dashboard/cart.html:229,253`.
   - Actual route: `carts/urls.py:8-11`.
   - Browser evidence: UI changed to quantity 2, database remained 1, 404/invalid JSON observed.
   - Severity: Medium.

2. **ISSUE FOUND — Signup confirmation enforcement**
   - Signup sets inactive in `dashboard/views.py:194-213`.
   - Live browser signup created `is_active=True` and login succeeded before a confirmation-token route was used.
   - `dashboard/views.py:507-517` later confirms the account and sets `email_confirmed=True`.
   - Severity: High/Medium.

3. **ISSUE FOUND — Clock element JavaScript error**
   - Browser console repeatedly reported `Cannot set properties of null (setting 'textContent')` on shop/dashboard/cart.
   - Severity: Low/Medium.

4. **ISSUE FOUND — Route/URL duplicate name risk**
   - Both carts and orders may expose checkout names under `/api/carts/` and `/api/orders/`.
   - `config/urls.py:31-33`, `carts/urls.py:1-11`, `orders/urls.py`.

5. **PARTIALLY VERIFIED — Oversized dashboard templates**
   - `dashboard/templates/dashboard/cart.html` and `shop.html` contain substantial inline CSS/JS, reducing separation and testability.
   - Severity: Medium.

6. **PARTIALLY VERIFIED — Repeated report matrices**
   - `coverage_matrix.md` and `security_compliance_matrix.md` duplicate most of the topic matrix.
   - Severity: Low.

7. **ISSUE FOUND — Stale hypothesis and README status**
   - `red_team/secureshop_tests/hypotheses.md` has H1/H3/H4/H5/H9/H13/H22 described as UNVERIFIED even though newer evidence exists.
   - `red_team/README.md:19-31` understates live and Naive Shop progress.
   - Severity: Medium.

8. **PARTIALLY VERIFIED — Hardcoded demo credentials**
   - Suitable for course demo; unacceptable if reused outside local development.
   - Severity: High for production, Low for isolated demo.

9. **NOT VERIFIED — Unnecessary/dead dependencies**
   - `requirements.txt` should be compared to imports and unused packages removed only after dependency analysis.
   - Severity: Low until verified.

10. **ISSUE FOUND — Exception handling**
   - Broad `except Exception` in checkout returns a generic failure.
   - `carts/views.py:153-157`
   - This is fail-safe but loses useful server diagnostics.

## 8. Integration and Testing

### Automated tests

**VERIFIED:** the Django test suite ran successfully: 16 tests passed.

**PARTIAL:** test suite coverage does not prove every feature requirement.

### Browser testing

**VERIFIED:** real browser sessions loaded:

- Signup and login
- Shop catalogue
- Valid search
- Product detail
- Nonexistent product
- Add to cart
- Cart page
- Checkout success
- Newsletter valid/duplicate/invalid
- Order history
- Customer/staff/admin newsletter admin page

**NOT VERIFIED:** full invalid quantity, remove, clear, profile edit, mobile layout, coupon reuse, second-order history and admin CRUD.

### Database

**VERIFIED:**

- PostgreSQL 16 vendor
- All migrations applied
- Disposable account id 18
- One checkout order id 18
- Newsletter subscriber and coupon created
- Cart cleared
- Lamp stock 30→29
- Disposable credit restored from 100→0

### Security behavior

**PARTIAL:**

- Existing evidence covers H5/H13/H19/H22 and H9.
- Browser evidence added for newsletter admin role boundaries.
- H4 live verified in browser/API.
- Cart route mismatch is now a concrete functional finding.
- H1/H2/H3/H16/H17 and attack scenarios still need final browser/database retests.

## 9. Severity and Priority

| Finding | Status | Severity | Priority |
|---|---|---|---|
| Cart quantity frontend/route mismatch | VERIFIED/ISSUE FOUND | Medium | Critical |
| Account confirmation enforcement inconsistency | VERIFIED/ISSUE FOUND | Medium | Critical |
| Stale hypothesis/report claims | ISSUE FOUND | Medium | High |
| Clock JS null-element error | ISSUE FOUND | Low/Medium | Medium |
| Demo credentials/default DB password | ISSUE FOUND/production risk | High in production | High before deployment |
| Oversized dashboard templates | PARTIALLY VERIFIED | Medium | Medium |
| Duplicate coverage matrices | ISSUE FOUND | Low | Medium |
| TOTP not enforced on seed accounts | PARTIALLY VERIFIED | Medium | High |
| Mobile/admin CRUD/browser coverage | NOT VERIFIED | Medium | High |

## 10. Recommended Remediation Order

1. Blue Team: align the cart quantity JS URL with `carts/urls.py`, or centralize a reverse URL.
2. Blue Team: decide and consistently enforce signup confirmation; align `/signup/` and `/dashboard/signup/`.
3. Blue Team: correct the shop/dashboard clock element or remove the repeated missing-element JS call.
4. Red Team: refresh stale hypotheses and matrices after live tests.
5. Red Team: collect final coupon reuse, insufficient-credit, profile and admin CRUD evidence.
6. Blue Team/Red Team: verify TOTP policy and whether it is required.
7. Blue Team: replace demo secrets/passwords for any non-local deployment.
8. Red Team: add an evidence index and a canonical report source set.

## 11. What Is Already Correct

- Django app structure is understandable and appropriately separated.
- Docker Compose, PostgreSQL, nginx and Gunicorn are integrated consistently.
- The web service is not directly published; nginx is the public TLS front door.
- Red Team tools are separate from Blue Team application code.
- Naive Shop is loopback-only and isolated from SecureShop database state.
- Live browser and database evidence is being captured in a dedicated evidence folder.
- Existing tests, static analysis and Naive Shop evidence are reproducible.

## 12. What Is Misplaced or Duplicated

- `coverage_matrix.md` overlaps `security_compliance_matrix.md`.
- Old hypothesis statuses overlap and contradict later regression reports.
- Browser evidence is not indexed comprehensively.
- Inline CSS/JS in dashboard templates belongs partially in assets or dedicated components.

## 13. What Is Missing

- Complete mobile UI verification.
- Complete profile/admin CRUD browser verification.
- Final coupon reuse and checkout retests.
- A final evidence index.
- A standalone Security Design Report.
- A verified Git commit-history section.
- A final consolidated report that distinguishes browser, automated and source-only evidence.

## 14. What Requires Manual Verification

- Confirmation enforcement before login.
- Cart quantity persistence.
- Cart removal/clear/session persistence.
- Invalid and oversized quantity input.
- Coupon one-use behavior.
- Store-credit rejection and successful checkout.
- Profile edits and password changes.
- Product/search/filter edge cases.
- Mobile layouts and navigation.
- Staff/admin Django and dashboard operations.
