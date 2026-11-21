# Test Case — Access Control / Authorization

**Lectures:** 2 (slide 24), 3 (Least Privilege, Separation of Duties), 6. **Hypotheses:** H5, H9, H15, H16, H18, H21, H22. **Status:** NOT TESTED (prepared).

> Note: Broken Access Control has strong **lecture** coverage but no dedicated Lab attack. Treated as Defense Validation / testing, pending the team's decision on whether it's a graded mandatory topic.

## Goal
Check object-level and role-level authorization across the API and dashboard.

## Preconditions
Local Blue build; test users: customer A, customer B, `staff`, `admin`; agreed window.

## Steps
1. **Orders IDOR (H5):** as A, GET/PATCH/DELETE an order owned by B (`/api/orders/orders/<B_id>/`).
2. **Missing auth (H9):** call `update-quantity` with no session.
3. **Category privilege (H15):** as customer A, POST `/api/products/ajax/add-category/`.
4. **Staff escalation (H16):** as `staff`, change another user's role, or attempt to delete `admin`.
5. **State-changing GET (H18):** GET the product-delete URL as staff.
6. **Logging (H21):** after the above, check whether any security event was logged.
7. **Misconfig (H22):** review `DEBUG`, `ALLOWED_HOSTS`, exposed `/api/docs/` on the final build.

## Expected (naive) vs secure
- **Naive:** cross-user access; non-admin writes; staff escalates; GET deletes; no logs.
- **Secure:** object-level checks (`get_queryset` filtered, object permissions); explicit roles; POST-only destructive actions; audit logging; hardened settings.

## Evidence → `evidence/access_control/`
Cross-user request/response; privilege-escalation attempt; settings review notes.

## Pass/Fail
- **FAIL:** any unauthorized read/write/escalation succeeds.
- **PASS:** blocked by object- and role-level checks.
