# Naive Shop Verification Audit

**Audit date:** 2026-11-22  
**Repository root:** `D:\software-sec-e-commerce-`  
**Branch:** `main`  
**Commit:** `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`  
**Scope:** Red Team Naive Shop verification only. No SecureShop or Blue Team testing was performed.

## 1. Files Inspected

- `naive_shop/app.py`
- `red_team/live_tests/attack_naive.py`
- `red_team/evidence/naive_shop/attack_results.md`
- `red_team/reports/naive_vs_secureshop_comparison.md`
- `red_team/docs/lab_checklist.md`
- `red_team/docs/lecture_checklist.md`
- `red_team/secureshop_tests/hypotheses.md`
- `red_team/evidence/README.md`

## 2. Naive Shop Architecture

`naive_shop/app.py` is a minimal, in-memory educational HTTP application using Python's standard library:

- Host: `127.0.0.1`
- Port: `8010`
- Server: `ThreadingHTTPServer`
- Storage: module-level `DB` dictionary
- Reset: `GET /reset`
- Framework: none
- Database: none
- Session framework: none
- Authentication: password lookup plus a client-controlled `user` cookie
- UI: a basic HTML home page and an unstyled admin table

The application is not a full SecureShop-style implementation. It provides no usable registration form, product-details route, search/filter workflow, shopping cart UI, newsletter feature, profile page, or checkout screen. It exposes most teaching scenarios through small HTTP APIs and two basic HTML pages.

### Routes and features

| Route | Method | Feature | Security/property |
|---|---|---|---|
| `/` | GET | Product list and login status | Minimal HTML UI |
| `/reset` | GET | Reset in-memory data | Disposable state |
| `/admin` | GET | User table | Deliberately open to everyone |
| `/api/login` | POST | Username/password login | Sets a trusted `user` cookie |
| `/api/checkout` | POST | Creates an unpaid order | Trusts client price |
| `/api/apply_coupon` | POST | Applies a coupon percentage | No per-user reuse tracking |
| `/api/orders/<id>` | GET | Reads an order | No ownership check |
| `/api/confirm?order=<id>` | GET | Confirms an order | No payment verification |

## 3. Controlled Execution

The server was started locally and bound to `127.0.0.1:8010`. The in-memory database was reset before testing. The existing script was run with authorization to update `red_team/evidence/naive_shop/attack_results.md`.

Execution command:

```text
python naive_shop/app.py
python red_team/live_tests/attack_naive.py
```

The server was stopped after verification.

## 4. Attack-by-Attack Results

### V1 — Client-controlled price

**Route:** `POST /api/checkout`  
**Input:** `{"product_id":1,"price":1}` with `Cookie: user=alice`

**Independent observed response:**

```text
HTTP/1.0 200 OK
{"order_id": 1, "charged": 1.0}
```

**Impact:** The server charged `$1.0` for the `$1337.00` Leather jacket. The actual order record stored `total: 1.0`.

**Classification:** COMPLETE for this local demonstration.

### V2 — Coupon reuse

**Route:** `POST /api/apply_coupon` twice

**Independent observed responses:**

```text
HTTP/1.0 200 OK
{"discount_percent":20,"new_subtotal":80.0}

HTTP/1.0 200 OK
{"discount_percent":20,"new_subtotal":80.0}
```

**Impact:** The same coupon can be applied twice and each response calculates another 20% discount. The app does not complete a purchase or track an applied coupon; its evidence demonstrates the coupon-calculation vulnerability, not a two-order revenue impact.

**Classification:** COMPLETE for coupon reuse at the calculation level; PARTIAL for completed coupon purchase/reuse.

### V3 — Broken access control / IDOR

**Route:** `GET /api/orders/1` with `Cookie: user=bob`

**Independent observed response:**

```text
HTTP/1.0 200 OK
{"id":1,"owner":"alice","product_id":1,"total":1.0,"paid":false}
```

**Impact:** Bob read Alice's order. Ownership was not checked.

**Classification:** COMPLETE.

### V4 — Insufficient workflow validation

**Before confirmation:** order 1 had `"paid": false`.  
**Action:** `GET /api/confirm?order=1` with Bob's cookie.

**Independent observed response:**

```text
HTTP/1.0 200 OK
{"confirmed":true,"order":{"id":1,"owner":"alice","product_id":1,"total":1.0,"paid":true}}
```

**Impact:** An unpaid order was marked paid without a payment operation.

**Classification:** COMPLETE.

### V5 — Client-controlled identity

**Action:** checkout with `Cookie: user=whoever`, then read the returned order.

**Independent observed responses:**

```text
HTTP/1.0 200 OK
{"order_id":2,"charged":1.0}

HTTP/1.0 200 OK
{"id":2,"owner":"whoever","product_id":1,"total":1.0,"paid":false}
```

**Impact:** Arbitrary username identity was accepted without authentication or server-side session binding.

**Classification:** COMPLETE.

### V6 — No login throttling

**Action:** Eight consecutive wrong-password login requests.

**Independent observed statuses:**

```text
[401, 401, 401, 401, 401, 401, 401, 401]
```

**Impact:** No lockout or attempt counter was triggered.

**Classification:** COMPLETE for the tested eight-request sequence.

### V7 — Broken access control

**Route:** `GET /admin` with no login cookie.

**Independent observed response:**

```text
HTTP/1.0 200 OK
```

The response displayed Alice, Bob and Admin records, including roles and store credit.

**Classification:** COMPLETE.

## 5. Existing Evidence Assessment

The existing evidence file is a current, generated summary:

- Timestamp: `2026-11-22T01:50:31.316015+00:00`
- Target: `127.0.0.1:8010`
- V1–V7 all assert and print successful response/state conditions.

Evidence quality remains mixed:

| Item | Evidence class | Reason |
|---|---|---|
| V1 | COMPLETE | Script assertion plus independently captured status/body and charged/total state |
| V2 | PARTIAL | Repeated 200 responses show reuse of discount calculation, but no completed purchase |
| V3 | COMPLETE | Actual 200 response exposed Alice's order to Bob |
| V4 | COMPLETE | Actual response changed `paid=false` to `paid=true` |
| V5 | COMPLETE | Arbitrary owner cookie produced an order owned by the forged identity |
| V6 | COMPLETE | Eight exact 401 responses prove no lockout for this sequence |
| V7 | COMPLETE | Actual unauthenticated 200 response exposed the user table |
| Existing summary file | PARTIAL | It is reproducible but does not include raw headers or all response bodies |

The screenshot files now present in `red_team/evidence/naive_shop/` support UI presentation:

- `naive-shop-home.png`
- `naive-shop-admin.png`

Screenshots alone do not replace raw HTTP evidence.

## 6. Attack Script Review

The existing `attack_naive.py` is executable and targets only `http://127.0.0.1:8010`.

Its checks are meaningful because it asserts:

- HTTP status or returned body value
- Charged price
- Coupon subtotal
- Order owner
- Paid state
- Forged identity owner
- Consecutive login status codes
- Unauthenticated admin content

The script writes to `red_team/evidence/naive_shop/attack_results.md`, overwriting that existing evidence file. This was explicitly authorized for this verification run.

It does not capture raw HTTP headers or full raw bodies in the evidence file. It only stores concise result summaries.

## 7. Usability and Course Demonstration Readiness

The Naive Shop is suitable as a compact, lab-specific demonstration of V1–V7, but it is **not sufficient for the official full project UI requirements**.

Missing complete usability/features:

- Registration and login UI
- Account confirmation
- Product-detail UI
- Search/filter UI
- Cart add/remove/quantity UI
- Newsletter signup UI and coupon issuance
- Coupon application and coupon reuse across real orders
- Store-credit checkout UI
- Order confirmation/history
- User profile
- Full admin management of users/products/coupons
- Mobile/responsive layout

Readiness result:

- **For V1–V7 attack demonstration:** READY
- **For full Naive Shop course deliverable:** NOT READY

## 8. CET431 Course Coverage

| Course topic | Naive Shop can demonstrate | Existing test | Executed | Raw evidence | SecureShop retest needed | Remaining gap |
|---|---|---|---|---|---|---|
| Excessive client-side trust | Yes | V1 script | Yes | Summary + independent status/body | Price read-only/server-side | Retain raw SecureShop price-tampering response |
| Coupon business rules | Yes, repeated calculation | V2 script | Yes | Summary + repeated 200 bodies | Coupon usage/replay across orders | Test a real first/second purchase |
| Exceptional input | No direct feature | None complete | No | None | Yes | Add quantity/input tests in SecureShop |
| Insufficient workflow validation | Yes | V4 script | Yes | Summary + paid-state response | Atomic payment/stock/credit workflow | Re-test confirmation and skipped checkout |
| 2FA broken identity/brute force | Partial identity; no real 2FA | V5/V6 script | Yes | Status/body summaries | TOTP enforcement/session identity | Build or validate real 2FA scenario |
| Authorization/IDOR | Yes | V3 script | Yes | 200 foreign-owner order body | Owner-scoped APIs/dashboard | Re-test multiple users and mutation |
| Least privilege/admin RBAC | Yes | V7 script | Yes | 200 admin table body | Customer/staff/admin boundaries | Compare live role screenshots |
| Password storage | No | None | No | None | Inspection/test | Not necessary unless course report requires |
| Account lockout/rate limit | Yes | V6 script | Yes | Eight 401 responses | 429/lockout in final SecureShop | Current final lockout result |
| Session/JWT replay | Partial cookie identity only | No real JWT script | No | V5 cookie evidence | Refresh blacklist/logout | Retest protected JWT replay |
| Non-repudiation/logging | No | None | No | None | Audit-log verification | Verify records and raw audit rows |
| Fail secure/resiliency | Partial | No complete scenario | No | None | Atomic failure behavior | Test invalid checkout/stock/credit paths |
| Behavioral anomaly detection | No | Lab demo only | No live Naive test | No raw attack evidence | Only if Blue Team implements | Mark N/A or document missing control |
| Location-based auth | No | Defense demo only | No live Naive test | None | Only if implemented | Not currently demonstrated |
| Time window/TOTP/HOTP | Partial TOTP in SecureShop; no Naive demo | Lab/demo files | No live Naive test | None | Test TOTP setup/enforcement/replay | Missing end-to-end MFA evidence |
| Passkeys/WebAuthn | No | None | No | None | Only if implemented | Missing |
| MFA fatigue/push | No | None | No | None | Optional/N/A unless taught as required | Document course status |
| SQL injection | No | No | No | None | SecureShop ORM/parameterized paths | Safe live search/API test |
| XSS | No | No | No | None | Template autoescaping and text rendering | Safe browser payload test |
| CSRF | No | No | No | None | CSRF middleware and cookie settings | Safe state-changing request test |
| TLS/transport | No | No | No | Browser HTTPS evidence exists from SecureShop | N/A for Naive loopback | Document local HTTP exception |
| Dependency/SCA | No | Static tools, separate | No current raw rerun | Existing reports only | Not a Naive comparison topic | Rerun only if required |
| STRIDE/DREAD/threat model | No direct scenario | Documentation work | No | Existing reports only | No SecureShop attack mapping | Produce final threat model and DREAD results |

## 9. Exact Next Steps

1. Keep V1–V7 as the core Naive Shop comparison only.
2. If the official requirement expects a full ecommerce UI, request an implementation phase to extend Naive Shop. This audit does not implement it.
3. Add raw HTTP request/response capture files for V1–V7 instead of a summary-only Markdown table.
4. Add browser screenshots for V1–V7 or at least for the UI/admin and each API state.
5. Improve V2 evidence to use two real order attempts or explicitly limit the claim to repeated coupon calculation.
6. Preserve the existing Naive evidence and add final rerun evidence rather than rewriting historical files when possible.
7. Retest H1-H4, H5, H9, H13, H22 and other course topics against the current SecureShop build.
8. Mark Labs 4–5 topics as N/A or PARTIAL unless SecureShop implements them.
9. Update the Naive vs SecureShop report with raw evidence links for both applications.
10. Consolidate the final Red Team evidence index, penetration report and deliverables checklist.
