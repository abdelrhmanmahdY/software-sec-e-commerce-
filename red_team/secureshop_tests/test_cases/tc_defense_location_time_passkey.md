# Test Case — Defense Validation: Location, Time, Passkey, TOTP

**Lab:** 5. **Type:** Defense Validation. **Status:** NOT APPLICABLE (prepared) — expected absent in the current app.

> These are **defenses**, not attacks. Not required by the PDF; validate only if the Blue Team implements them.

## Goal
Determine whether SecureShop implements any of: passkey/WebAuthn, geo/impossible-travel, login time window, or TOTP MFA — and whether each is correct.

## Steps
1. Ask for the code location of each control. None → **NOT APPLICABLE**.
2. **Passkey:** server verifies signature **and** credential id, checks origin/challenge; test the recovery flow (can an attacker enroll a new passkey?).
3. **Location:** used as one signal + MFA, not a sole allow-list; test a VPN exit inside the allowed region.
4. **Time window:** enforced server-side; test the boundary (hour 22 blocked, 8 allowed).
5. **TOTP:** rate-limited; tracks last-used step; test replay of a sniffed code within its 30 s window.

## Expected
- **Absent:** NOT APPLICABLE.
- **Present & correct:** each gate enforced server-side; TOTP non-replayable; passkey origin-bound.
- **Present & weak:** e.g. TOTP replay within window, or location as sole gate → finding.

## Evidence → `evidence/defense_location_time_passkey/`
Code locations, boundary-test results, TOTP replay result.
