# SecureShop Hypotheses (ALL UNVERIFIED)

These come from **reading the current code only**. None has been tested. Every one stays `UNVERIFIED` until confirmed during an authorized testing window against the Blue Team's final version.

Fields per hypothesis: ID, endpoint/feature, why suspected (code), safe future test steps, expected security result, estimated severity (DREAD), status.

> **Severity is estimated** (DREAD sum in brackets) and will be re-rated after real testing. `Local?` = can be self-tested locally now (with your go-ahead) vs needs the Blue final version + window.

---

### H1 — Checkout creates an order without covering the total
- **Endpoint/feature:** `POST /api/carts/orders/checkout/` (`carts/views.py:95–152`)
- **Why suspected:** `credit_used = min(store_credit, total)`; the order is created regardless of whether credit covered `total`, and `use_store_credit` can be false.
- **Safe test steps:** customer with $100 credit, cart > $100; call checkout with `use_store_credit` true then false; inspect whether an order was created and the credit balance.
- **Expected result:** order placed without full payment → financial loss.
- **Severity:** High (12). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.3 (workflow), [tc_t4](test_cases/tc_t4_workflow_validation.md).

### H2 — Second checkout endpoint has no payment/stock/coupon logic
- **Endpoint/feature:** `POST /api/orders/checkout/` (`orders/views.py:19–44`)
- **Why suspected:** creates an order and clears the cart with no price, payment, or stock check.
- **Safe test steps:** JWT for a test customer; POST; inspect created order and stock.
- **Expected result:** free order; duplicate/again workflow bypass.
- **Severity:** High (12). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.3, [tc_t4](test_cases/tc_t4_workflow_validation.md).

### H3 — Coupon can be reused; no used-coupon tracking
- **Endpoint/feature:** checkout `coupon_code` (`carts/views.py:100–109`), `users/models.py:16–23`
- **Why suspected:** coupon looked up and applied; nothing records that it was used or limits reuse. (Note: only one coupon field per request, so Lab 2.1 *alternating stacking* may not apply directly — must test.)
- **Safe test steps:** apply the same coupon on two separate orders; check both got the discount.
- **Expected result:** unlimited coupon reuse → revenue loss.
- **Severity:** Medium (10). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.1, [tc_t2](test_cases/tc_t2_coupon_rules.md).

### H4 — Newsletter coupon codes are predictable and unauthenticated
- **Endpoint/feature:** `POST /dashboard/newsletter/signup/` (`dashboard/views.py:445–448`)
- **Why suspected:** `coupon_code = f"NEWS{User.objects.count():04d}"` — guessable, and signup needs no login/verification.
- **Safe test steps:** subscribe with a few test emails; observe the generated codes; try to predict the next.
- **Expected result:** attacker predicts valid coupon codes.
- **Severity:** Medium (9). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.1, [tc_t2](test_cases/tc_t2_coupon_rules.md).

### H5 — Orders API is not scoped to the owner (IDOR)
- **Endpoint/feature:** `/api/orders/orders/`, `/api/orders/order-items/` (`orders/views.py:9–17`)
- **Why suspected:** `queryset = Order.objects.all()`, `IsAuthenticated` only, no `get_queryset` filter or object permission.
- **Safe test steps:** two test users A and B; as A, GET/PATCH/DELETE an order belonging to B by id.
- **Expected result:** any user reads/modifies others' orders → Broken Access Control (A01).
- **Severity:** High (13). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 2 slide 24, Lecture 3 (Least Privilege), [tc_access_control](test_cases/tc_access_control.md).

### H6 — Client can set `price` / `status` on the Orders API
- **Endpoint/feature:** `OrderItem` create via `/api/orders/order-items/` (`orders/serializers.py:6–9`, `11–18`, `24–30`)
- **Why suspected:** `price` is a writable field; `status` not restricted on create.
- **Safe test steps:** POST an order-item with a chosen `price`; read back the stored value.
- **Expected result:** attacker sets their own price → same class as Lab 1.
- **Severity:** High (12). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 1, [tc_t1](test_cases/tc_t1_client_side_price.md).

### H7 — Unvalidated cart quantity (negative / zero / huge / non-int)
- **Endpoint/feature:** `cart/add/`, `update-quantity/`, shop POST (`carts/views.py:36,44,67`; `dashboard/views.py:390`)
- **Why suspected:** `int(request.data.get("quantity",1))`; `cart_item.quantity += quantity`; behavior depends on DB constraint (SQLite vs Postgres differ).
- **Safe test steps:** send quantity = -5, 0, 999999, "abc"; observe stored quantity, totals, and errors. **Test on the same DB as the final version.**
- **Expected result:** negative totals / integer issues / DoS via huge values.
- **Severity:** Medium (10). **Status:** UNVERIFIED. **Local?** partial → then window.
- **Maps to:** Lab 2.2 (exceptional input), [tc_t3](test_cases/tc_t3_exceptional_input.md).

### H8 — Exception details leaked to the client
- **Endpoint/feature:** `update-quantity`, checkout (`carts/views.py:77–78`, `153–154`)
- **Why suspected:** `return JsonResponse({"error": str(e)})` exposes internal error text.
- **Safe test steps:** send malformed JSON / bad item_id; read the error body.
- **Expected result:** information disclosure (stack/DB hints).
- **Severity:** Low (8). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 5 slide 34, OWASP A10 (mishandling exceptions), [tc_t3](test_cases/tc_t3_exceptional_input.md).

### H9 — `update-quantity` missing `login_required`
- **Endpoint/feature:** `POST /api/carts/cart/update-quantity/` (`carts/views.py:62–63`)
- **Why suspected:** only `@require_POST`; no auth decorator (relies on `cart__user=request.user`, which is `AnonymousUser` if unauthenticated).
- **Safe test steps:** POST without a session; observe status/behavior.
- **Expected result:** unauthenticated access / error leakage; Complete Mediation gap.
- **Severity:** Medium (9). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 3 (Complete Mediation), [tc_access_control](test_cases/tc_access_control.md).

### H10 — Frontend/route mismatches (functional, report to Blue)
- **Endpoint/feature:** `cart.html:229/253` → `/api/cart/update-quantity/` (real path differs); duplicate `checkout` url name.
- **Why suspected:** JS path doesn't match `carts/urls.py`; name clash across apps.
- **Safe test steps:** open the cart page locally; watch DevTools network for 404s.
- **Expected result:** broken quantity update (functional bug, not security).
- **Severity:** N/A (functional). **Status:** UNVERIFIED. **Local?** yes.
- **Maps to:** report to Blue Team.

### H11 — Account confirmation bypass on `/signup/`
- **Endpoint/feature:** `POST /signup/` (`users/views.py:26–28`)
- **Why suspected:** form path calls `form.save()` without `is_active=False`; also `csrf_exempt`. User may be active immediately, unlike the dashboard signup.
- **Safe test steps:** register via `/signup/`; try to log in without confirming.
- **Expected result:** confirmation step bypassed (inconsistent with other signups).
- **Severity:** Medium (10). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.3 (workflow), [tc_t5](test_cases/tc_t5_auth.md).

### H12 — Confirmation link shown to user; reusable within 3 days
- **Endpoint/feature:** `signup_view`, `confirm_email` (`dashboard/views.py:125–128`, `417–430`)
- **Why suspected:** the signed URL is displayed to the user via a message; `max_age=3 days`; token not single-use.
- **Safe test steps:** use the same token twice; use after an admin deactivates the account.
- **Expected result:** token replay re-activates an account.
- **Severity:** Low (8). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.3, [tc_t5](test_cases/tc_t5_auth.md).

### H13 — No rate limiting / lockout on login
- **Endpoint/feature:** `/dashboard/login/`, `/api/auth/login/` (`settings.py:101–111` has no throttle)
- **Why suspected:** no DRF throttle classes, no lockout; brute force feasible.
- **Safe test steps:** a **small, bounded** number of wrong attempts on a throwaway test account, localhost only. Never a full sweep.
- **Expected result:** password/credential brute force possible.
- **Severity:** High (12). **Status:** UNVERIFIED. **Local?** yes (bounded) → then window.
- **Maps to:** Lab 3 + Lecture 4 slide 20, [tc_t5](test_cases/tc_t5_auth.md).

### H14 — Username enumeration on signup
- **Endpoint/feature:** signup forms (`users/forms.py:7–13`, default `UserCreationForm`)
- **Why suspected:** "A user with that username already exists" distinguishes valid usernames. (Login form is likely generic — must confirm.)
- **Safe test steps:** register an existing vs new username; compare messages.
- **Expected result:** account enumeration aids targeted attacks.
- **Severity:** Low (8). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 5 slide 34, [tc_t5](test_cases/tc_t5_auth.md).

### H15 — Any logged-in user can create a category; endpoint is `csrf_exempt`
- **Endpoint/feature:** `POST /api/products/ajax/add-category/` (`products/views.py:35–43`)
- **Why suspected:** `@login_required` but no staff check; `@csrf_exempt`.
- **Safe test steps:** as a normal customer session, POST a new category name.
- **Expected result:** privilege gap (non-admin writes catalog data); CSRF surface.
- **Severity:** Medium (9). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 3 (Least Privilege), [tc_access_control](test_cases/tc_access_control.md).

### H16 — Staff (non-superuser) can change roles / delete other users
- **Endpoint/feature:** `user_update_role`, `admin_user_delete` (`dashboard/views.py:77–100`)
- **Why suspected:** gated only by `is_staff`; a staff user could promote themselves or others, or delete an admin.
- **Safe test steps:** as the seeded `staff` user, change another user's role / attempt delete.
- **Expected result:** privilege escalation; Separation of Duties violation.
- **Severity:** High (12). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 3 slide 4, Lecture 6 (Separation of Duties), [tc_access_control](test_cases/tc_access_control.md).

### H17 — Customer can create an order and choose its status
- **Endpoint/feature:** `POST /dashboard/orders/create/` (`dashboard/views.py:280–292`, `users/forms.py:62–65`)
- **Why suspected:** `OrderForm` exposes `status`; a user could create an order already "Completed".
- **Safe test steps:** as a customer, POST order create with `status=Completed`; inspect.
- **Expected result:** workflow/integrity bypass.
- **Severity:** Medium (9). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.3, [tc_t4](test_cases/tc_t4_workflow_validation.md).

### H18 — Product delete may accept GET (CSRF)
- **Endpoint/feature:** `product_delete` (`dashboard/views.py:254–260`)
- **Why suspected:** deletes without an explicit POST check in the view body.
- **Safe test steps:** as staff, issue a GET to the delete URL; observe.
- **Expected result:** state-changing GET → CSRF risk.
- **Severity:** Low (7). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Optional (CSRF), [tc_access_control](test_cases/tc_access_control.md).

### H19 — JWT stays valid after logout (no blacklist)
- **Endpoint/feature:** SimpleJWT (`config/urls.py:38–39`; no `SIMPLE_JWT`/blacklist in settings)
- **Why suspected:** no token blacklist app; access tokens valid until expiry even after logout.
- **Safe test steps:** obtain a token, "log out", reuse the token on `/api/users/me/`.
- **Expected result:** session/token replay (Lecture 5 slide 12).
- **Severity:** Medium (10). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 5 (session hijacking), [tc_t5](test_cases/tc_t5_auth.md).

### H20 — Password hashing is Django default (PBKDF2), not Argon2/bcrypt
- **Endpoint/feature:** no custom `PASSWORD_HASHERS` in `settings.py`
- **Why suspected:** lecture recommends Argon2id/bcrypt; Django default is PBKDF2 (salted, iterated — acceptable, but worth noting).
- **Safe test steps:** inspection only — read a hash prefix in the local DB.
- **Expected result:** **not necessarily a vulnerability**; note for the report.
- **Severity:** Low (6). **Status:** UNVERIFIED. **Local?** yes (inspection).
- **Maps to:** Lecture 4 slides 9–15, [tc_t5](test_cases/tc_t5_auth.md).

### H21 — No security/audit logging
- **Endpoint/feature:** whole repo (needs a `logging` search on the final version)
- **Why suspected:** no logging config observed; attacks may go unrecorded.
- **Safe test steps:** search the final code for logging; attempt an action and check logs.
- **Expected result:** non-repudiation / accountability gap (Lecture 2 slides 25–28).
- **Severity:** Low (7). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lecture 2 (Non-repudiation), [tc_access_control](test_cases/tc_access_control.md).

### H22 — Security misconfiguration
- **Endpoint/feature:** `settings.py:10–12`, `config/urls.py:19–20,42–43`
- **Why suspected:** fallback `SECRET_KEY`, `ALLOWED_HOSTS=['*']`, public Swagger schema; depends on final deployment.
- **Safe test steps:** review final settings; check `DEBUG`, hosts, exposed schema.
- **Expected result:** info disclosure / weakened defenses.
- **Severity:** Medium (9). **Status:** UNVERIFIED. **Local?** needs final config.
- **Maps to:** Optional (A05/A02), [tc_access_control](test_cases/tc_access_control.md).

### H23 — Seed coupon has no expiry despite claimed validity window
- **Endpoint/feature:** `seed_data.py:139–141` vs output line 157
- **Why suspected:** `expires_at=None` but the message says "valid from 2026-06-01 to 2026-08-31".
- **Safe test steps:** apply `SUMMER2026` after the claimed end date; see if accepted.
- **Expected result:** expired-coupon acceptance.
- **Severity:** Low (7). **Status:** UNVERIFIED. **Local?** yes → then window.
- **Maps to:** Lab 2.1, [tc_t2](test_cases/tc_t2_coupon_rules.md).

---

## Summary table

| ID | Area | Est. severity | Status |
|---|---|---|---|
| H1 | Checkout payment | High | UNVERIFIED |
| H2 | Free checkout endpoint | High | UNVERIFIED |
| H3 | Coupon reuse | Medium | UNVERIFIED |
| H4 | Predictable coupon | Medium | UNVERIFIED |
| H5 | Orders IDOR | High | UNVERIFIED |
| H6 | Client-set price | High | UNVERIFIED |
| H7 | Cart quantity | Medium | UNVERIFIED |
| H8 | Error leakage | Low | UNVERIFIED |
| H9 | Missing auth on endpoint | Medium | UNVERIFIED |
| H10 | Frontend mismatch (functional) | N/A | UNVERIFIED |
| H11 | Confirmation bypass | Medium | UNVERIFIED |
| H12 | Token replay | Low | UNVERIFIED |
| H13 | No login rate-limit | High | UNVERIFIED |
| H14 | User enumeration | Low | UNVERIFIED |
| H15 | Category privilege/CSRF | Medium | UNVERIFIED |
| H16 | Staff privilege escalation | High | UNVERIFIED |
| H17 | Order status choose | Medium | UNVERIFIED |
| H18 | Delete via GET | Low | UNVERIFIED |
| H19 | JWT after logout | Medium | UNVERIFIED |
| H20 | PBKDF2 (note) | Low | UNVERIFIED |
| H21 | No audit logging | Low | UNVERIFIED |
| H22 | Misconfiguration | Medium | UNVERIFIED |
| H23 | Coupon expiry | Low | UNVERIFIED |
