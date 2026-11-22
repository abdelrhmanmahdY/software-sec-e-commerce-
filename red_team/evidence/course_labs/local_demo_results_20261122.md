# Course Lab Demo Execution Results

- **Executed:** 2026-11-22 (local project checkout)
- **Target:** Offline local Python examples only; no network, SecureShop, database, or external lab was accessed.
- **Purpose:** Verify that the checked-in educational examples execute and record their observed output. These results do not prove SecureShop behavior.

## Lab 1 — client-side price trust

Command: `python red_team/labs/lab1_client_side_trust/naive_price_demo.py`

Observed:

```text
Store credit: $100.00
Real jacket price: $1,337.00
[NAIVE ] charged $0.01  -> order allowed: True   (VULNERABLE)
[SECURE] charged $1,337.00  -> order allowed: False   (SAFE)
```

**Classification:** DEMO verified. In-memory function comparison only.

## Lab 2.1 — coupon stacking

Command: `python red_team/labs/lab2_business_logic/coupon_replay_demo.py`

Observed: alternating two codes eight times resulted in a **100%** naive discount; the local secure function capped it at **30%**.

**Classification:** DEMO verified. This is not a completed purchase or evidence about SecureShop coupon redemption.

## Lab 2.2 — exceptional input / email truncation

Command: `python red_team/labs/lab2_business_logic/email_truncation_demo.py`

Observed: a 274-character sample was truncated by the naive function to a value whose domain comparison granted admin; the secure function rejected it as too long.

**Classification:** DEMO verified. No account or role was created.

## Lab 2.3 — workflow validation

Command: `python red_team/labs/lab2_business_logic/workflow_skip_demo.py`

Observed: naive confirmation transitioned an unpaid `CART` order to `CONFIRMED`; the secure function rejected that transition, then allowed the simulated legitimate path after payment.

**Classification:** DEMO verified. No real order or credit was changed.

## Lab 3.1 — 2FA identity and attempt limits

Command: `python red_team/labs/lab3_authentication/auth_identity_demo.py`

Observed: the in-memory naive model accepted a forged target identity and found its randomly generated four-digit code after **3,660 attempts**. The secure model kept identity bound to the session and stopped after one attempt in this execution.

**Classification:** DEMO verified. This is a local simulation, not a PortSwigger run or a SecureShop brute-force test. The generated code is intentionally not retained.

## Lab 4 — behavioral anomaly scoring

Command: `python red_team/labs/lab4_anomaly_detection/anomaly_detection_demo.py`

Observed: the sample legitimate timing was allowed (`z=2.79`); the sample paste-bot and slow-attacker timings were flagged (`z=24.02` and `z=34.95`).

**Classification:** DEMO verified for the included z-score exercise only. It does not implement the complete Lab 4.1 live keystroke enrollment/replay experiment or prove a SecureShop control.

## Lab 5 — location, time, and passkey checks

Command: `python red_team/labs/lab5_location_time_passkey/defense_checks_demo.py`

Observed: the nearby location was inside the sample radius; London was outside. The sample time window allowed hours 8 and 21 and blocked 22 and 3. The Boolean passkey model allowed only `(credential_matches=True, signature_valid=True)`, and the combined examples blocked the sample location, time, and signature failures.

**Classification:** DEMO verified for the printed logic only. The passkey check is Boolean simulation, not WebAuthn/FIDO signature verification; this script does not generate or verify a TOTP/HOTP code.
