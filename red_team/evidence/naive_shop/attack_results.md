# Naive Shop - Attack Results (all vulnerabilities confirmed)

- Timestamp: 2026-11-22T01:50:31.316015+00:00
- Assertions verify observed response/state; coupon result proves repeated discount calculation, not completed discounted purchases.
- Target: `http://127.0.0.1:8010` (intentionally insecure demo)

| ID | Vulnerability | Status | Detail |
|---|---|---|---|
| V1 | Client-controlled price | CONFIRMED VULNERABILITY | checkout charged $1.0 for the $1337 jacket |
| V2 | Coupon reuse (no tracking) | CONFIRMED VULNERABILITY | same coupon accepted twice: 20% then 20% again |
| V3 | IDOR (read other user's order) | CONFIRMED VULNERABILITY | bob fetched alice's order #2 -> HTTP 200, owner='alice' |
| V4 | Workflow bypass (confirm unpaid) | CONFIRMED VULNERABILITY | order #2 marked paid=True with no payment |
| V5 | Client-controlled identity | CONFIRMED VULNERABILITY | the 'user' cookie is trusted unchanged; no server-side session |
| V6 | No login throttling | CONFIRMED VULNERABILITY | 8 bad logins all returned {401} - never locked out |
| V7 | Broken access control (/admin open) | CONFIRMED VULNERABILITY | GET /admin with no login -> HTTP 200 (full user table) |
