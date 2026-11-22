# Naive Shop vs SecureShop — Current Comparison

Naive Shop V1–V7 were executed against `http://127.0.0.1:8010`. SecureShop entries below are only the properties tested in disposable in-memory SQLite or the Django unit suite; they are **not** live HTTPS/PostgreSQL results. Historical live claims are not treated as current evidence.

| # | Course topic | Attack | Naive Shop result | SecureShop result |
|---|---|---|---|---|
| 1 | Client-side trust | Submit a lower checkout price | **PASS** — order persisted at $1 for the $1337 jacket | **PARTIALLY VERIFIED** — order-item price/status unit test passed in the in-memory suite; live checkout retest NOT TESTED. |
| 2 | Coupon reuse | Apply a coupon twice | **PASS** — repeat requests each returned a discount | **VERIFIED IN-MEMORY** — one redemption succeeded; replay returned 400 and checked state was unchanged. |
| 3 | IDOR | Read another user's order | **PASS** — Bob retrieved Alice's order | **VERIFIED IN-MEMORY** — owner list/detail and customer-mutation tests passed; live retest NOT TESTED. |
| 4 | Workflow validation | Confirm an order without paying | **PASS** — unpaid order became paid without payment | **NOT TESTED** as the same bypass; in-memory checkout integrity was tested, but no equivalent payment-bypass attempt was made. |
| 5 | Authentication identity | Forge identity via a client cookie | **PASS** — `user` cookie identity was accepted | **VERIFIED IN-MEMORY** — forged cookie did not authenticate and profile returned 302. However, password-only JWT for a TOTP-enabled account is a confirmed open finding. |
| 6 | Brute-force protection | Repeat invalid login attempts | **PASS** — eight invalid attempts followed by a valid login | **PARTIALLY VERIFIED** — password lockout unit tests pass. TOTP IP lockout works with test-only schema; clean migrations omit `AuthThrottle`. |
| 7 | Least privilege / admin | Reach admin without authorization | **PASS** — anonymous response exposed admin data | **VERIFIED IN-MEMORY** — unauthenticated admin redirected to login; unauthenticated API docs returned 403; role tests passed. |

## Reading the comparison
The Naive Shop is the intentionally vulnerable comparison target. SecureShop results are reported with their actual test environment; a unit or in-memory result is not described as live deployment evidence.

## How to reproduce
```
# Naive Shop (starts it if needed; V1-V7 use loopback only)
python red_team/live_tests/run_naive_suite.py

# SecureShop: isolated tests only; live regression requires a separate disposable clone
python red_team/live_tests/run_isolated_audit_tests.py
python red_team/live_tests/verify_inmemory_security.py
```
