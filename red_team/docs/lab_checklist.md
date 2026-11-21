# Lab Checklist — Labs 1–5

A review list for every exercise in the Labs: its type, status, and the walkthrough link.

| Lab | Exercise | Topic | Type | Status | Walkthrough |
|---|---|---|---|---|---|
| 1 | Excessive trust in client-side controls | Business Logic | Practical Attack | Ready (DEMO) | [lab1](../labs/lab1_client_side_trust/walkthrough.md) |
| 2.1 | Flawed enforcement of business rules (coupons) | Business Logic | Practical Attack | Ready (DEMO) | [lab2](../labs/lab2_business_logic/walkthrough.md) |
| 2.2 | Inconsistent handling of exceptional input | Business Logic | Practical Attack | Ready (DEMO) | [lab2](../labs/lab2_business_logic/walkthrough.md) |
| 2.3 | Insufficient workflow validation | Business Logic | Practical Attack | Ready (DEMO) | [lab2](../labs/lab2_business_logic/walkthrough.md) |
| 3.1 | 2FA broken logic + client-controlled identity + brute force | Authentication | Practical Attack | Ready (DEMO) | [lab3](../labs/lab3_authentication/walkthrough.md) |
| 4.1 | Anomaly behavior detection (z-score) | Behavioral auth | Defense Validation | Ready (DEMO) | [lab4](../labs/lab4_anomaly_detection/walkthrough.md) |
| 4.2 | Keystroke-dynamics challenge | Behavioral auth | Defense Validation | Ready (DEMO) | [lab4](../labs/lab4_anomaly_detection/walkthrough.md) |
| 5 | Location / Time window / Passkey / TOTP | Composite auth | Defense Validation | Ready (DEMO) | [lab5](../labs/lab5_location_time_passkey/walkthrough.md) |

## Notes

- **Labs 1–3** teach **attacks** → we reproduce them and prepare offensive test cases for SecureShop.
- **Labs 4–5** teach **defenses** → we prepare **defense validation**: how the Red Team confirms the defense exists and works, without assuming it is there in the first place.
- "Ready (DEMO)" = the walkthrough and the local example are written. The real evidence (PortSwigger screenshots) needs a manual step from you.

## Business Logic — full list (Lab 1 slide 18)

The lab listed 11 business-logic types. Only **4** were practically applied (the ones above). The rest are **Mentioned Only**:

2. High-level logic vulnerability — *Mentioned Only*
3. Inconsistent security controls — *Mentioned Only*
5. Low-level logic flaw — *Mentioned Only*
7. Weak isolation on a dual-use endpoint — *Mentioned Only*
9. Authentication bypass via flawed state machine — *Mentioned Only*
10. Infinite money logic flaw — *Mentioned Only*
11. Authentication bypass via encryption oracle — *Mentioned Only*

> The name-only ones are **not** treated as required standalone attacks (per your instructions). But we may run into instances of them while testing SecureShop (e.g. #10 "infinite money" is close to the coupon flaw H3).
