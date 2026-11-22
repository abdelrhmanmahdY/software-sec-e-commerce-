# Red Team Evidence Index

**Updated:** 2026-11-22  
Evidence is grouped by target and execution type. Historical evidence is not presented as a current live-deployment result.

| Evidence | Target / method | What it supports | Status / limits |
|---|---|---|---|
| [`naive_attack_20261122T021321Z.md`](../evidence/naive_shop/naive_attack_20261122T021321Z.md) | Naive Shop, local HTTP on `127.0.0.1:8010` | Raw V1–V7 requests and responses with order-state reads | Current captured run; V2 only proves repeated discount calculation; V6 proves no visible lockout response in eight attempts. |
| [`naive_attack_20261122T020814Z.md`](../evidence/naive_shop/naive_attack_20261122T020814Z.md) | Naive Shop, local HTTP | Earlier V1–V7 transcript | Preserved historical run. |
| `naive-shop-home.png`, `naive-shop-admin.png` | Naive Shop screenshots | UI appearance and unauthenticated admin disclosure | Screenshots do not replace request/response or state evidence. |
| [`local_demo_results_20261122.md`](../evidence/course_labs/local_demo_results_20261122.md) | Offline Python lab demonstrations | Executed outputs for the included course demo scripts | Demonstrates examples only; not SecureShop or web workflow behavior. |
| [`backend_results.json`](../evidence/review/backend_results.json) and [`backend_run.txt`](../evidence/review/backend_run.txt) | Historical Django Client + PostgreSQL transaction | Prior IDOR, business-rule, validation, RBAC, MFA, and rollback outcomes | Historical run at 2026-11-22 00:28 UTC; `rollback_verified=true`; not a live browser/current-HEAD deployment retest. Direct-order result is inconclusive. |
| [`phase1_inmemory_registration_mfa_20261122.md`](../evidence/review/phase1_inmemory_registration_mfa_20261122.md) | Current-checkout Django TestClient + in-memory SQLite | Registration activation inconsistency and password-only JWT access for a TOTP-enabled fixture | Current source behavior reproduced without persistent data; not browser, TLS, or external-service evidence. |
| `05-nonexistent-product-404.png`, `06-cart-quantity-404.png`, `07-checkout-success.png`, `08-post-checkout-shop.png` | Historical SecureShop browser screenshots | Specific page states observed in the previous Phase-B workflow | Do not infer complete workflow, request details, or database state from screenshots alone. |
| [`official_course_security_coverage.md`](official_course_security_coverage.md) | Course topic matrix | Links topics to scenarios, source observations, evidence, and retest actions | Many rows remain partial/not started; this is not a completion claim. |
| [`phase_one_attack_evidence.md`](phase_one_attack_evidence.md) | Evidence assessment | Attack-by-attack quality and test boundaries | Distinguishes current, historical, and simulation evidence. |

## Preservation notes

- Existing `attack_results.md` and prior reports are retained and were not regenerated.
- Naive Shop evidence contains disposable in-memory demo identities; it must not be confused with real users.
- Do not retain JWTs, passwords, confirmation tokens, or real account data in future evidence.
- The screenshots and historical database export are not sufficient proof of every functional requirement.
