# Test Case — T1: Client-side price trust

**Lab:** 1. **Hypotheses:** H6, H1. **Status:** NOT TESTED (prepared).

## Goal
Check whether SecureShop trusts any client-supplied price/total instead of recomputing from the catalog.

## Preconditions
- Local Blue Team build running on `http://localhost:8000`.
- Throwaway test accounts (customer). Agreed testing window.

## Steps
1. Authenticate (JWT or session) as the test customer.
2. **Orders API (H6):** `POST /api/orders/order-items/` (or the final order-create endpoint) with a body that includes `price` set to a low value (e.g. `0.01`). Record request + response.
3. Read the order back (`GET /api/orders/orders/<id>/`) and check the stored `price`.
4. **Cart/checkout (H1):** add an expensive item; at `POST /api/carts/orders/checkout/` try injecting `price`/`total`/`subtotal` fields in the JSON body.
5. Compare the charged amount vs the real catalog price.

## Expected (naive) vs secure
- **Naive:** server stores the attacker's price → undercharge.
- **Secure:** server ignores client price, uses `Product.price`; `price` is read-only in the serializer.

## Evidence to save → `evidence/t1/`
Request with tampered price, response, stored value screenshot.

## Pass/Fail
- **FAIL (vuln confirmed):** stored/charged price equals the attacker value.
- **PASS (secure):** server recomputes; tampered field ignored or rejected.
