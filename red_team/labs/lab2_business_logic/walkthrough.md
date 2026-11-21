# Lab 2 — Business Logic (three exercises)

**Course reference:** Lab 2 (updated). Three business-logic vulnerabilities.
**Type:** Practical Attack.
**Status:** Walkthroughs ready (DEMO). Real PortSwigger evidence needs a manual step from you.

Exercises:
- 2.1 Flawed enforcement of business rules (coupons)
- 2.2 Inconsistent handling of exceptional input (email truncation)
- 2.3 Insufficient workflow validation (skip payment)

---

## Lab 2.1 — Flawed enforcement of business rules (coupons)

### Vulnerability
The app only rejects a coupon if it equals the **last** one applied. So alternating between two codes applies each one again and again, stacking the discount with no cap.

### Objective
Buy the leather jacket by driving the total below your store credit with stacked discounts.

### Attack, step by step (`wiener : peter`)
1. Note the coupon `NEWCUST5` shown on the site.
2. Sign up to the newsletter at the bottom of the page → you get a second coupon `SIGNUP30`.
3. Add the jacket, go to checkout, apply both coupons — total drops once per code.
4. Apply the **same** code twice in a row → rejected ("already applied").
5. Now **alternate**: `NEWCUST5`, `SIGNUP30`, `NEWCUST5`, `SIGNUP30` … each one is accepted, discount keeps stacking.
6. Keep going until the total is below your credit, place the order. Lab solved.

### Root cause
"Each coupon used once" is enforced by remembering only the **most recent** code. No set of all applied codes, and no cap on total discount.

### Defense
- Store **all** applied coupons on the order; reject any code already in that set.
- Enforce one use per code and a maximum total discount, server-side.
- Re-validate the full cart, discounts, and total at checkout.
- Demo: `coupon_replay_demo.py`.

### SecureShop test case
[`tc_t2_coupon_rules.md`](../../secureshop_tests/test_cases/tc_t2_coupon_rules.md). Hypotheses **H3**, **H4**, **H23**.

---

## Lab 2.2 — Inconsistent handling of exceptional input

### Vulnerability
Registration accepts a very long email but stores only the first **255** characters. A crafted address can be truncated so it ends as `@dontwannacry.com`, which grants admin access.

### Objective
Reach the admin panel and delete the user `carlos`.

### Attack, step by step
1. Find `/admin` (Burp → Site map → Discover content, or browse directly in Community). Access denied, but it says DontWannaCry users have access.
2. Open registration — it asks DontWannaCry employees to use their company email. Note your unique lab email domain.
3. Register with a local part at least 200 characters long; confirm via the email client.
4. Log in → My account shows the email truncated to 255 chars.
5. Register again with a long email that includes `dontwannacry.com` as a subdomain, sized so the final `m` of `@dontwannacry.com` is exactly character 255.
6. Confirm, log in → you now have admin. Delete `carlos`. Lab solved.

### Root cause
The same input is handled differently in two places: the full address sends the email, but only 255 chars are stored. Admin is granted from the email domain instead of an explicit role.

### Defense
- Enforce one maximum length at the start; **reject** over-long input instead of silently truncating.
- Validate the exact value that will be stored and used.
- Never grant privileges from an email domain — assign roles explicitly.
- Test exceptional input: very long, empty, special values.
- Demo: `email_truncation_demo.py`.

### SecureShop test case
[`tc_t3_exceptional_input.md`](../../secureshop_tests/test_cases/tc_t3_exceptional_input.md). Hypotheses **H7**, **H8**.

---

## Lab 2.3 — Insufficient workflow validation

### Vulnerability
The app assumes you only reach the order-confirmation page after a successful checkout, and never verifies the order was paid for.

### Objective
Buy the jacket by abusing the purchasing workflow.

### Attack, step by step (`wiener : peter`)
1. Buy any affordable item once.
2. In HTTP history, see that `POST /cart/checkout` redirects to an order-confirmation page. Send `GET /cart/order-confirmation?order-confirmation=true` to Repeater.
3. In the browser, add the jacket to the cart. Do **not** check out (too expensive).
4. In Repeater, resend the confirmation request. The order completes without the cost being deducted. Lab solved.

### Root cause
No server-side workflow/state validation: the confirmation step runs without completing checkout, and never checks that payment succeeded.

### Defense
- Track order state on the server; allow confirmation only after payment succeeds.
- Verify cart total and payment at the final step.
- Bind confirmation to a unique, unguessable order ID tied to the session.
- Test by skipping, repeating, and reordering workflow steps.
- Demo: `workflow_skip_demo.py`.

### SecureShop test case
[`tc_t4_workflow_validation.md`](../../secureshop_tests/test_cases/tc_t4_workflow_validation.md). Hypotheses **H1**, **H2**, **H11**, **H12**.

---

## Evidence to collect (manual), under `evidence/lab2/`
Per exercise: the key captured request(s), the tampered Repeater request + response, and the "lab solved" banner.
