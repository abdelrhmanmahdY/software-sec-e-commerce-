# Official Functional Requirements Compliance Matrix

**Audit date:** 2026-11-22  
**Environment:** SecureShop at `https://localhost` (Django 5.2.4, PostgreSQL 16)  
**Boundary:** Read-only audit of Blue Team code/database; no application fixes or data changes were made.

## Evidence key

- **PASS** — end-to-end browser/database verification completed.
- **PARTIAL** — some workflow steps or evidence exist, but the complete requirement is not verified.
- **NOT TESTED** — no reproducible end-to-end verification performed.
- **FAIL** — broken or missing in an observed workflow.

| Official requirement | Points | Status | Live/browser evidence | Database or source evidence | Missing work |
|---|---:|---|---|---|---|
| Registration, account confirmation, login, logout | 5 | PARTIAL | Admin, staff, and `admin@example.test`/`customer` login flows were browser-tested. Logout was reached and redirected to login. Registration/confirmation invalid-account behavior remains untested. | `dashboard/views.py:110,190,194`; signup confirmation code exists. Live seed accounts verified. | Test registration, confirmation link, confirmed/unknown input, and repeat/invalid confirmation. |
| Product catalogue, details, search/filter | 4 | PARTIAL | Customer shop page loaded 4 products. Product detail/search/filter pages were not fully exercised end-to-end. | `products/models.py`; `dashboard/views.py:444,563`; 4 live products. | Browser test details, search, filters, no-result state, and nonexistent product. |
| Cart add/remove/quantity/session persistence | 4 | PARTIAL | Logged-in customer shop loaded with cart count. Customer cart page and an existing cart can exist, but add/remove/quantity/session persistence were not proven. | Live customer cart had 2 items in the earlier database snapshot; `carts/models.py`, `dashboard/views.py:424-437`. | Add/remove/quantity; refresh/re-login session persistence; cross-user cart protection. |
| Newsletter signup and coupon issuance/application | 3 | PARTIAL | Newsletter form is visible on the shop, but successful subscription/coupon issuance was not completed. | 6 live newsletter rows; signup code at `dashboard/views.py:521`; coupon usage code exists. | Submit valid/duplicate/invalid newsletter; verify DB row/coupon; apply once and reuse. |
| Store-credit checkout and order confirmation/history | 5 | NOT TESTED | No successful or rejected checkout workflow was browser-tested. | Checkout source and live order rows exist. | Browser checkout, insufficient credit, invalid quantity/coupon, confirmation and order history. |
| User profile view/edit and owner-only orders | 3 | PARTIAL | Profile route was reachable and a browser profile tab existed in one session. No edit was verified. | `dashboard/views.py:222,226`; live 5 profiles. | Edit valid/invalid values; save and reload; cross-user order/profile denial. |
| Admin management of users/products/coupons | 4 | PARTIAL | Admin account reached Django dashboard and the newsletter subscriber changelist. Staff reached a staff dashboard. Customer and unauthenticated Django URLs were denied. | Django admin registrations for users/coupons/newsletter; 5 live users and 5 coupons. | Browser-test user, product, coupon create/edit/delete and role boundaries. |
| Desktop/mobile usability | 2 | NOT TESTED | Desktop browser was used and shop/admin pages rendered. Mobile viewport was not tested. | Responsive CSS/templates exist. | Run mobile viewport and navigation/form usability checks. |
| Error handling/navigation | 2 | PARTIAL | 403 and login/redirect behavior was observed. JS console reported missing clock element on shop/dashboard. | Django and templates exist. | Document safe valid/invalid errors and resolve or record the JS console defects. |

**Functionality status:** 0 PASS, 6 PARTIAL, 5 NOT TESTED, 0 FAIL. This is conservative because implementation without a reproducible browser/database workflow is not awarded full credit.

