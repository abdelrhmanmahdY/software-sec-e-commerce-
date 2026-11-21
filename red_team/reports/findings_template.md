# Findings — SecureShop Red Team

Use this template for **each** finding. Do not mark anything CONFIRMED before an authorized real test. Copy the block per finding.

> Current state: **no confirmed findings.** All items are prepared from the hypotheses in `../secureshop_tests/hypotheses.md` and stay UNVERIFIED until the testing window.

---

## Finding template

- **Finding ID:** RT-00X
- **Vulnerability:** <short name>
- **Course Reference:** <Lab / Lecture + slide>
- **Affected Feature:** <cart / checkout / orders / login / admin ...>
- **Affected Endpoint:** <method + path>
- **Severity (DREAD):** <Low/Medium/High> (D_, R_, E_, A_, D_ = sum) — *estimated until confirmed*
- **Description:** <what the flaw is, plainly>
- **Reproduction Steps:**
  1. <step>
  2. <step>
- **Request used:**
  ```
  <raw HTTP request — real, captured during the test>
  ```
- **Result / Response:**
  ```
  <actual response>
  ```
- **Evidence:** `evidence/<topic>/<file>`
- **Actual Impact:** <what an attacker gains>
- **Root Cause:** <the underlying design/code reason>
- **Recommended Fix (for Blue Team):** <concrete change>
- **Testing Status:** NOT TESTED | INCONCLUSIVE | CONFIRMED

---

## Example (illustrative — NOT a real result)

- **Finding ID:** RT-001
- **Vulnerability:** Orders API object-level authorization missing (IDOR)
- **Course Reference:** Lecture 2 slide 24 (AuthZ), Lecture 3 (Least Privilege)
- **Affected Feature:** Orders
- **Affected Endpoint:** `GET /api/orders/orders/<id>/`
- **Severity (DREAD):** High (D3,R3,E2,A3,D2 = 13) — estimated
- **Description:** Any authenticated user may read/modify another user's order because the queryset is not scoped to the owner.
- **Reproduction Steps:** *(to be filled during the window — currently NOT TESTED)*
- **Request used:** *(capture the real request)*
- **Result / Response:** *(capture the real response)*
- **Evidence:** `evidence/access_control/`
- **Actual Impact:** Disclosure/tampering of other customers' orders.
- **Root Cause:** `queryset = Order.objects.all()` with only `IsAuthenticated`.
- **Recommended Fix:** Override `get_queryset` to filter by `request.user`; add object-level permission.
- **Testing Status:** NOT TESTED
