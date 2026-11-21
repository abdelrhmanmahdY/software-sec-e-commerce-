# Test Case — T2: Coupon business rules

**Lab:** 2.1. **Hypotheses:** H3, H4, H23. **Status:** NOT TESTED (prepared).

## Goal
Check coupon reuse, predictable newsletter codes, and expiry enforcement.

## Preconditions
Local Blue build; test customer; agreed window.

## Steps
1. **Reuse (H3):** apply the same valid coupon on two separate orders. Record both totals.
2. **Multiple codes in one order:** if the final checkout accepts more than one coupon, try applying two, and try the alternating sequence from Lab 2.1.
3. **Predictable codes (H4):** subscribe to the newsletter with 3 test emails; record each returned code; try to predict and redeem the next.
4. **Expiry (H23):** redeem `SUMMER2026` (or final seed coupon) after its claimed end date; check acceptance.

## Expected (naive) vs secure
- **Naive:** coupon reusable; codes guessable; expired code accepted; discounts stack with no cap.
- **Secure:** one use per code tracked on the order; random codes; expiry enforced; total discount capped.

## Evidence → `evidence/t2/`
Both order totals, the sequence of generated codes, the expired-redemption response.

## Pass/Fail
- **FAIL:** reuse works, or next code predicted, or expired code accepted.
- **PASS:** each blocked server-side.
