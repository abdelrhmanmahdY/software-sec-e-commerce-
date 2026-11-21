# Test Case — Defense Validation: Behavioral Anomaly Detection

**Lab:** 4. **Type:** Defense Validation. **Status:** NOT APPLICABLE (prepared) — expected absent in the current app.

> This is a **defense**, not an attack. The PDF does not require it; validate it only if the Blue Team claims to implement it.

## Goal
Determine whether SecureShop implements login anomaly/behavioral detection, and if so, whether it's correct and replay-resistant.

## Steps
1. Ask the Blue Team for the control's code location. If none exists → record **NOT APPLICABLE** and stop.
2. If present: confirm it learns only from **trusted** logins (can't be poisoned).
3. Check the threshold and std-floor are reasonable (triggers on paste/bot, not on every user).
4. **Replay test (Lecture 5 slide 13):** capture a legit timing pattern and replay it via script; see if the engine is fooled.
5. Check cold-start handling for a brand-new user.

## Expected
- **Absent:** NOT APPLICABLE (not required).
- **Present & correct:** anomalous logins get step-up/block; replay is caught by device/fingerprint binding + continuous re-scoring.
- **Present & weak:** static-profile replay passes → finding.

## Evidence → `evidence/defense_behavioral/`
Code location note, threshold values, replay result.
