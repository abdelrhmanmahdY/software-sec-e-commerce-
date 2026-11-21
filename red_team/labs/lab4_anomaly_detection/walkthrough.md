# Lab 4 — Behavioral Anomaly Detection (Defense Validation)

**Course reference:** Lab 4.1 and 4.2 + Lecture 4 (slides 32–34) + Lecture 5 (slides 8–13).
**Type:** Defense Validation (this lab teaches a **defense**, not an attack).
**Status:** Walkthrough + demo ready (DEMO).

> Important: this is a defensive mechanism. The Red Team's job is **not** to assume SecureShop has it — it's to check whether it exists, and if so, whether it's implemented correctly. SecureShop (Django) almost certainly does **not** ship keystroke anomaly detection, so the expected outcome is "control not present / NOT APPLICABLE" unless the Blue Team adds it.

---

## 1. The idea (plain)

Classic auth asks "who are you?" once. Behavioral detection keeps asking "does this still act like you?" using features like typing speed and the gaps between keys. It learns each user's normal behavior, then flags logins that are statistically far from normal (a likely account takeover) → ALLOW / step-up MFA / BLOCK.

## 2. The one idea you need — the z-score

```
z = | value - mean | / std
```
- `mean` = average of past (trusted) values — the center of "normal".
- `std`  = standard deviation — how much it normally varies.
- `z ≈ 0` normal; `z > 3` rare/suspicious.
- Average the per-feature z-scores into one anomaly score; above a threshold (lab uses 3.0) → challenge/block.

## 3. How the Red Team validates this defense

If the Blue Team claims behavioral/anomaly detection exists, verify it — don't take the claim:

| Check | How | Pass looks like |
|---|---|---|
| Control exists | Ask for the code location; read it | A real scoring function on login |
| Learns from **trusted** logins only | Inspect how history is built | Attacker can't poison the profile |
| Reasonable threshold | Read the threshold + std floor | Not so loose it never triggers, not so tight it locks everyone |
| Replay-resistant | Try replaying captured timings (Lecture 5 slide 13) | Bound to device/browser fingerprint too, re-scored mid-session |
| Cold-start handled | Check a brand-new user | No crash, no "allow everything" |

> If the control is **absent**, that's not a finding by itself — behavioral auth isn't required by the PDF. Record it as **NOT APPLICABLE** unless the team decided to implement it.

## 4. Replay attack (the weakness to test, Lecture 5 slide 13)

A static profile can be fooled: capture a legit user's timing with a keylogger, then replay that exact pattern via a script. If the engine only compares similarity to a stored static profile, the replay matches. Defenses: bind to device/browser fingerprint, continuously re-score, detect "too-perfect" timing, treat it as one input in a risk engine.

## 5. Run the local demo

```powershell
python red_team/labs/lab4_anomaly_detection/anomaly_detection_demo.py
```
It builds a profile from sample typing times, then scores: a legit (slightly tired) user → ALLOW; a pasting bot → BLOCK; a slow attacker → BLOCK. This is the Lab 4.2 exercise, completed.

## 6. Lessons / answers (Lab 4 hand-in questions)

- **Why is averaging z-scores risky when one feature has a much larger scale?** A large-scale feature (e.g. distance in km) can dominate the average, so one big feature hides or exaggerates the others. Fix: normalize each feature, or weight them, before averaging.
- **Brand-new user with no history?** Cold start — there's no "normal" yet. Don't trust the score; collect enough trusted logins first, or fall back to another factor (MFA).

## 7. SecureShop relevance
[`tc_defense_behavioral.md`](../../secureshop_tests/test_cases/tc_defense_behavioral.md). Expected status for the current app: **NOT APPLICABLE** (control not present) until the Blue Team adds it.
