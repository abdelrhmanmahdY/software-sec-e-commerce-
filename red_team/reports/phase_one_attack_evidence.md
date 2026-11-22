# CET431 Phase One — Red Team Attack Evidence

**Review date:** 2026-11-22  
**Repository:** `D:\software-sec-e-commerce-`  
**Branch / HEAD:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`  
**Scope:** Existing Naive Shop attacks, offline course demonstrations, prior SecureShop database tests, and current-checkout isolated Django request-client checks. No SecureShop production/source changes or persistent database writes were made.

## Evidence classification

| Test | Target / method | Result and impact evidence | Classification / limitation |
|---|---|---|---|
| V1 — client-controlled price | Naive Shop at `http://127.0.0.1:8010`; captured HTTP requests/responses and subsequent order read | Checkout accepted client price `$1` for the `$1337` seeded jacket; stored order total was `$1`. | **COMPLETE** for this in-memory Naive Shop scenario; not a SecureShop result. |
| V2 — coupon reuse | Naive Shop; same coupon submitted twice | Both submissions returned the same 20% discount. | **PARTIAL**: proves repeat calculation acceptance, not two completed purchases, coupon accounting, or realized balance impact. |
| V3 — order IDOR | Naive Shop; Bob requested Alice's order | Response disclosed the Alice-owned order and contents. | **COMPLETE** for the demonstrated read scenario; in-memory data. |
| V4 — payment/workflow bypass | Naive Shop; read unpaid order, then confirmation request | Order changed from `paid=false` to `paid=true` without payment. | **COMPLETE** for this state transition; no real payment or persistent data. |
| V5 — client-controlled identity | Naive Shop; forged `user` cookie | Checkout/order response attributed an order to the supplied identity without authentication. | **COMPLETE** for the demonstrated identity flow. |
| V6 — login throttling | Naive Shop; eight invalid logins | All eight returned 401; no lockout response was observed. | **PARTIAL**: the script did not follow with a valid login or inspect a lockout state, so it establishes no visible response change rather than all possible throttling behavior. |
| V7 — open admin page | Naive Shop; unauthenticated `GET /admin` | HTML response exposed the seeded user/role/credit table. | **COMPLETE** for the demonstrated unauthenticated disclosure. |
| Course Labs 1–5 examples | Local Python demonstrations; no network or application database | Captured printed outputs for the included price, coupon, truncation, workflow, identity, timing, location/time, and Boolean passkey examples. | **DEMO VERIFIED**, not application attack evidence; Lab 4/5 examples are deliberately limited simulations. |
| Prior SecureShop IDOR, price, coupon, checkout, input, role, and MFA tests | Historical Django Client tests against PostgreSQL in a transaction | [`backend_results.json`](../evidence/review/backend_results.json) records request outcomes, fixture state, and `rollback_verified=true`. | **HISTORICAL DB-BACKED EVIDENCE** from 2026-11-22 00:28 UTC; not a live-browser run and not independently repeated against the current HEAD. The direct-order workflow row is INCONCLUSIVE. |
| Registration confirmation paths | Current-checkout Django `TestClient`, isolated SQLite `:memory:` | `/signup/` returned 302 but persisted an active account with `email_confirmed=false`; `/dashboard/signup/` returned 302 and API signup returned 201 with inactive accounts. | **CURRENT-CHECKOUT REQUEST-CLIENT VERIFIED**; not browser/live-service evidence. Account rows were process-local only. |
| MFA enforcement on JWT login | Current-checkout Django `TestClient`, isolated SQLite `:memory:` | Password-only login for a TOTP-enabled fixture returned 200 with an access token; the token accessed the protected order list (200). | **CURRENT-CHECKOUT REQUEST-CLIENT VERIFIED — CONFIRMED GAP**. No real account, persistent data, or retained token. |

The current-checkout isolated checks and their limitations are documented in [`phase1_inmemory_registration_mfa_20261122.md`](../evidence/review/phase1_inmemory_registration_mfa_20261122.md).

## Naive Shop raw capture

The primary transcript is [`naive_attack_20261122T021321Z.md`](../evidence/naive_shop/naive_attack_20261122T021321Z.md). It contains 20 captured HTTP exchanges, including the reset and login preconditions, attack requests, response headers/bodies, and state reads. Password values are redacted. This run targeted only the source-pinned local listener `127.0.0.1:8010`; the listener was stopped after testing.

The older `attack_results.md` remains a historical summary. Do not treat it as a raw transcript or overwrite it. An earlier raw run is also preserved at [`naive_attack_20261122T020814Z.md`](../evidence/naive_shop/naive_attack_20261122T020814Z.md).

## SecureShop comparison boundary

The historical PostgreSQL transaction tests are valuable evidence for the build they exercised, but they do not prove the live HTTPS deployment or the exact current checkout. The latest stored findings include a confirmed password-only JWT/MFA bypass and an inconclusive direct-order workflow. Current-checkout in-memory request tests now independently confirm the MFA gap and the registration-route inconsistency, but neither establishes proxy/TLS/browser behavior.

No finding is upgraded to “fixed” or “prevented” without a current retest after Blue Team changes. See [`official_course_security_coverage.md`](official_course_security_coverage.md) for course-topic mapping and retest needs.
