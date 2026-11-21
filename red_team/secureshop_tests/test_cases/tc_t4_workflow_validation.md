# Test Case — T4: Workflow validation

**Lab:** 2.3. **Hypotheses:** H1, H2, H11, H12, H17. **Status:** NOT TESTED (prepared).

## Goal
Check whether order/payment/confirmation steps can be skipped, repeated, or reordered.

## Preconditions
Local Blue build; test customer with limited store credit; agreed window.

## Steps
1. **Pay-less checkout (H1):** cart total above credit; call `POST /api/carts/orders/checkout/` with `use_store_credit` true then false; check if an order is created and the credit balance.
2. **Free endpoint (H2):** call `POST /api/orders/checkout/`; check order creation with no payment/stock logic.
3. **Confirmation replay (Lab 2.3):** if the final app has an order-confirmation step, capture it and resend without completing payment.
4. **Confirmation bypass / token replay (H11, H12):** register via `/signup/` and try to log in without confirming; reuse a confirmation token twice.
5. **Status choice (H17):** create an order with `status=Completed` as a customer.

## Expected (naive) vs secure
- **Naive:** order placed without payment; confirmation reachable without checkout; token reusable; customer sets status.
- **Secure:** server tracks order state; confirmation requires PAID; single-use token; status is server-controlled.

## Evidence → `evidence/t4/`
Each request + response; credit balance before/after; created order states.

## Pass/Fail
- **FAIL:** any order completes without proper payment/workflow.
- **PASS:** blocked server-side at each step.
