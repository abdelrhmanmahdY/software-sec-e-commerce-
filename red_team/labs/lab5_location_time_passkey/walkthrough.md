# Lab 5 — Location, Time, and Passkeys (Defense Validation)

**Course reference:** Lab 5 (all) + Lecture 5 (slides 16–43).
**Type:** Defense Validation (teaches **defenses**, not attacks).
**Status:** Walkthrough + demo ready (DEMO).

> Same as Lab 4: these are defenses. The Red Team checks whether they exist and are correct, and does **not** assume SecureShop uses them. A plain Django shop won't have passkeys / geo / time-window gates unless the Blue Team added them → expected **NOT APPLICABLE** otherwise.

---

## 1. The idea (plain)

Lab 5 keeps the password and adds three independent checks, evaluated in order; the first miss blocks the login:

1. **Passkey (FIDO2/WebAuthn):** the server stores a public key; the authenticator signs this login's challenge. A valid signature **and** matching credential id are both required.
2. **Location:** login point must be within 50 km of the enrolled home (haversine distance).
3. **Time:** local hour must be in `[8, 22)` (window does not wrap past midnight). TOTP is the other time-based proof — a 6-digit code that changes every 30 s.

Decision order (from the lab): `passkey` → `location` → `time`. First failure wins.

## 2. Why each check, briefly

- **Passkey:** origin-bound signatures can't be phished or replayed to a look-alike site (Lecture 5 slides 39–43). The weak point attackers target is **account recovery**, not the crypto.
- **Location:** geography is a free risk signal; "impossible travel" (Cairo 09:00 → London 09:30) is physically impossible. But it's **not** an identity factor — VPNs/proxies defeat it, so it's one signal, never the sole gate.
- **Time/TOTP:** TOTP = HMAC-SHA1(secret, unix_time // 30), truncated to 6 digits; ±1 window tolerates clock drift. Weakness: shared secret on the server; no "last used step" check means a sniffed code is replayable within its window.

## 3. How the Red Team validates these defenses

| Control | What to check | Weakness to probe |
|---|---|---|
| Passkey | Server verifies signature **and** credential id, checks origin/challenge/rpId | Recovery flow (can an attacker enroll a new passkey?) |
| Location | Used as **one** signal + MFA, not a sole allow-list | VPN exit inside the allowed region |
| Time window | Enforced server-side; sensible hours | Off-by-one at the boundary (hour 22) |
| TOTP | Rate-limited; tracks last-used step (no replay) | Replay a sniffed code within its 30 s window |

If a control is **absent**, record **NOT APPLICABLE** — it isn't required by the PDF unless the team chose it.

## 4. Run the local demo

```powershell
python red_team/labs/lab5_location_time_passkey/defense_checks_demo.py
```
It reproduces the Lab 5 printout: haversine distances (0.0 / 4.3 / 3511.3 km), the time window (hours 8, 21 ALLOW; 22, 3 BLOCK), a passkey check (only `True,True` passes), and four combined logins. It uses only `math` (no crypto libraries, no network).

## 5. The hands-on three functions (Lab 5, 3 marks)

Implemented in the demo:
- `haversine_km(lat1, lon1, lat2, lon2)` — distance in km.
- `time_allowed(hour, start, end)` — `start <= hour < end`.
- `passkey_allowed(credential_matches, signature_valid)` — both must be true.

## 6. SecureShop relevance
[`tc_defense_location_time_passkey.md`](../../secureshop_tests/test_cases/tc_defense_location_time_passkey.md). Expected status for the current app: **NOT APPLICABLE** until the Blue Team adds any of these controls.
