# SecureShop Live Baseline Results

- Target: `http://127.0.0.1:8000` (local, authorized baseline)
- Source: `red_team/live_tests/run_live_tests.py` (real HTTP, stdlib only)
- Note: INITIAL BASELINE against an unfinished app. Not a final finding set.

| Test | Hyp | Status | Detail |
|---|---|---|---|
| T-UP Server reachable | - | TESTED - NOT VULNERABLE | GET / -> HTTP 200 |
| T-AUTH JWT login (customer) | - | TESTED - NOT VULNERABLE | POST /api/auth/login/ -> HTTP 200, got access token |
| T-SWAGGER API docs exposed without auth | H22 | CONFIRMED VULNERABILITY | GET /api/docs/ (no auth) -> HTTP 200 |
| T-UPDQTY-NOAUTH update-quantity requires auth | H9 | TESTED - NOT VULNERABLE | no-auth POST -> HTTP 403 |
| T-ERRLEAK Error body leaks internals | H8 | INCONCLUSIVE | body[:160]='<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta http-equiv="content-type" content="text/html; charset=utf-8">\n  <meta name="robots" content="NONE,NOARCHIVE">\n  ' |
| T-PROD-READ Product list readable | - | TESTED - NOT VULNERABLE | GET /api/products/products/ -> HTTP 200 |
| T-ORDERS-LIST Orders list scope (manual review) | H5 | INCONCLUSIVE | GET /api/orders/orders/ -> HTTP 200; needs a 2nd user's order to confirm IDOR. body[:200]='{"count":2,"next":null,"previous":null,"results":[{"id":3,"user":4,"status":"Pending","created_at":"2026-11-21T17:23:39.524124Z","updated_at":"2026-11-21T17:23:39.524140Z","items":[{"id":3,"product":1' |
| T-ORDERS-IDOR Read order id=1 as customer | H5 | INCONCLUSIVE | GET /api/orders/orders/1/ -> HTTP 200; confirm ownership of id=1 to classify (CONFIRMED if it belongs to another user). |
| T-RATELIMIT Login lockout / throttling (6 tries) | H13 | CONFIRMED VULNERABILITY | 6 bad logins -> statuses [401, 401, 401, 401, 401, 401]; no lockout/throttle observed |
| T-NEWSLETTER Newsletter coupon predictability | H4 | CONFIRMED VULNERABILITY | issued codes ['NEWS0003', 'NEWS0003']; pattern NEWS#### = predictable |
| T-CHECKOUT-PAY Checkout without covering total | H1 | NOT TESTED | changes data / spends credit / destructive - run manually on a recoverable DB during the agreed window (see test_cases/). |
| T-CHECKOUT-FREE Free checkout endpoint | H2 | NOT TESTED | changes data / spends credit / destructive - run manually on a recoverable DB during the agreed window (see test_cases/). |
| T-COUPON-REUSE Coupon reuse across orders | H3 | NOT TESTED | changes data / spends credit / destructive - run manually on a recoverable DB during the agreed window (see test_cases/). |
| T-PRICE-TAMPER Client-set order item price | H6 | NOT TESTED | changes data / spends credit / destructive - run manually on a recoverable DB during the agreed window (see test_cases/). |
| T-STAFF-ESC Staff role escalation / delete | H16 | NOT TESTED | changes data / spends credit / destructive - run manually on a recoverable DB during the agreed window (see test_cases/). |
