# Test Case — T5: Authentication

**Lab:** 3. **Hypotheses:** H11, H12, H13, H14, H19, H20. **Status:** NOT TESTED (prepared).

## Goal
Check identity handling, rate limiting, enumeration, token lifecycle, and password storage.

## Preconditions
Local Blue build; **throwaway** test accounts only; agreed window.

> **Safety:** any brute-force style check must be a **small, bounded** number of attempts (e.g. ≤ 20) on a throwaway account, localhost only. Never a full sweep, never a shared/graded instance.

## Steps
1. **Client-controlled identity (H / Lab 3):** inspect login/any 2FA flow for identity values carried in client-controlled fields/cookies; try changing them.
2. **Rate limit / lockout (H13):** a bounded set of wrong passwords on a test account; check for lockout/throttle.
3. **Enumeration (H14):** register/login with an existing vs unknown username; compare messages and timing.
4. **JWT after logout (H19):** obtain a token, log out, reuse it on `/api/users/me/`.
5. **Confirmation (H11, H12):** as in T4 steps 4.
6. **Password storage (H20):** inspection — read a hash prefix in the local DB (expect `pbkdf2_...`); note recommendation vs Argon2/bcrypt.

## Expected (naive) vs secure
- **Naive:** identity trusted from client; no lockout; distinct error messages; token valid after logout.
- **Secure:** identity server-side; lockout + throttle; generic errors; token blacklist on logout; strong hashing.

## Evidence → `evidence/t5/`
Request/response pairs; lockout behavior; the two different enumeration messages; token-replay result.

## Pass/Fail
- **FAIL:** identity forgeable, or no lockout, or token replay works.
- **PASS:** each control present and effective.
