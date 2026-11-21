# Test Case — T3: Exceptional input

**Lab:** 2.2. **Hypotheses:** H7, H8. **Status:** NOT TESTED (prepared).

## Goal
Check how SecureShop handles out-of-range, empty, over-long, and wrong-type input.

## Preconditions
Local Blue build; test customer; agreed window. **Use the same DB engine as the final version** (SQLite vs PostgreSQL enforce `PositiveIntegerField` differently).

## Steps
1. **Cart quantity (H7):** on `cart/add/`, `update-quantity/`, and shop POST, send `quantity` = `-5`, `0`, `999999999`, `"abc"`, `1.5`. Record stored quantity, totals, and status.
2. **Over-long fields:** registration email/username/first_name with 200–300+ chars; check truncation vs rejection (Lab 2.2 idea).
3. **Empty/missing fields:** omit required fields; send empty JSON body.
4. **Error leakage (H8):** send malformed JSON to `update-quantity`/checkout; read the error body for `str(e)` internals.

## Expected (naive) vs secure
- **Naive:** negative/huge quantities stored; silent truncation; raw exception text returned.
- **Secure:** strict validation (min 1, max cap, integer); reject over-long; one hard length limit; generic error messages.

## Evidence → `evidence/t3/`
Each boundary request + response; the leaked-error body.

## Pass/Fail
- **FAIL:** any invalid value accepted, or internal error text exposed.
- **PASS:** validated and rejected with a generic message.
