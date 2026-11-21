# SecureShop Regression Results (hardened build)

- Target: `https://localhost` (local HTTPS, authorized)
- Source: `red_team/live_tests/run_regression.py` (property-based, stdlib)
- Each row checks the real security property, not just a status code.

| Test | Former finding | Status | Detail |
|---|---|---|---|
| T-UP HTTPS reachable | - | TESTED - DEFENSE HELD | GET / -> 302 |
| T-H22 API docs require auth | H22 | TESTED - DEFENSE HELD | GET /api/docs/ (no auth) -> 403 (expected 401/403) |
| T-AUTH customer JWT login | - | TESTED - DEFENSE HELD | token issued |
| T-H5-list Orders list owner-scoped | H5 | TESTED - DEFENSE HELD | list -> 200; only own orders returned |
| T-H5-detail Read another user's order id=3 | H5 | TESTED - DEFENSE HELD | GET /orders/3/ (not owner) -> 404 (blocked) |
| T-H6-price Non-staff cannot set item price | H6 | TESTED - DEFENSE HELD | customer POST order-items price=0.01 -> 403 (expected 403) |
| T-H19 Refresh token revoked on logout | H19 | TESTED - DEFENSE HELD | reuse blacklisted refresh -> 401 (expected 401) |
| T-H13 Login lockout after repeated failures | H13 | TESTED - DEFENSE HELD | 7 failed logins -> [401, 401, 401, 401, 401, 429, 429] (expect a 429) |
| T-H9 Cart update requires auth | H9 | TESTED - DEFENSE HELD | no-auth update-quantity -> 403 (expected 401/403) |
