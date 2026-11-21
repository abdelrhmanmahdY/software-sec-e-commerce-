# Lecture Checklist — Lectures 1–6

A comprehensive list of every security topic mentioned in the lectures, classified. The categories:

- **Practical Attack** — a topic we can build an attack/test for.
- **Defense Validation** — a defensive mechanism we verify exists and works.
- **Security Principle** — a principle we use to explain the root cause.
- **Methodology** — an assessment / threat-modeling method.
- **Optional / Mentioned Only** — named but not covered enough.

> Rule: we do **not** turn every theoretical topic into a required attack just because it was mentioned.

---

## Lecture 1 — Introduction & CIA

| Topic | Slide | Category | Linked to |
|---|---|---|---|
| CIA Triad (Confidentiality/Integrity/Availability) | 14–17 | Security Principle | all findings |
| Defects / Bugs / Flaws / Vulnerabilities / Risk | 13 | Security Principle | finding classification |
| Assets / Threats / Attackers inventory | 18 | Methodology | Threat model |
| OWASP Top 10 (2021 vs 2025) | 20–21 | Methodology | matrix mapping |
| AAAA (Authentication/Authorization/Auditing/Action) | 22 | Security Principle | A5, B1, B5 hypotheses |
| Threats vs Requirements (STRIDE-ish) | 23–24 | Methodology | Threat model |

## Lecture 2 — Security in Every Phase + STRIDE/DREAD

| Topic | Slide | Category | Linked to |
|---|---|---|---|
| SDLC / Shift-left security | 5–12 | Security Principle | — |
| **STRIDE** threat model | 11 | Methodology | Threat model in the pentest report |
| **DREAD** prioritization | 13–14 | Methodology | severity in each finding |
| Authorization (RBAC, Read/Write/Delete) | 24 | Defense Validation | H5, H15, H16 |
| Non-repudiation | 27–28 | Defense Validation | H21 (logging) |

## Lecture 3 — Security Principles

| Topic | Slide | Category | Linked to |
|---|---|---|---|
| Least Privilege | 2–3 | Security Principle | H5, H15, H16 |
| Minimize Common Mechanism (individual accounts + RBAC) | 4 | Security Principle | H16 |
| Defense in Depth | 7 | Security Principle | general |
| Fail Secure / Resiliency | 8 | Security Principle | H1, H8 |
| Diversity | 9 | Security Principle | — |
| Open Design (no security by obscurity) | 11 | Security Principle | H22 |
| Complete Mediation (from Kahoot) | L6 | Security Principle | H5, H9, H11 |
| Separation of Duties (from Kahoot) | L6 | Security Principle | H16 |
| Psychological Acceptability | L3 img | Security Principle | — |

## Lecture 4 — Authentication Methods (part 1)

| Topic | Slide | Category | Linked to |
|---|---|---|---|
| AuthN vs AuthZ vs Non-repudiation | 3 | Security Principle | — |
| NIST AAL levels | 4 | Methodology | rating auth strength |
| Password storage (Argon2/bcrypt, salt, pepper) | 9–15 | Defense Validation | H20 |
| Password cracking (dictionary/mask, fast hashes) | 15 | Practical Attack (offline, educational) | H20 |
| Account lockout / rate-limit | 9, 20 | Defense Validation | H13 |
| PINs & Security Questions | 16–20 | Optional / Mentioned Only | — |
| Smart cards / OTP tokens (challenge-response) | 22–26 | Optional / Mentioned Only | — |
| Biometrics (FAR/FRR) | 28–31 | Defense Validation | — (not used in SecureShop) |
| Behavioral biometrics (keystroke) | 32–34 | Defense Validation | Lab 4 |

## Lecture 5 — Authentication Methods (part 2)

| Topic | Slide | Category | Linked to |
|---|---|---|---|
| Behavioral biometrics replay attack | 12–13 | Practical Attack | Lab 4 defense validation |
| Location-based (impossible travel) | 16–21 | Defense Validation | Lab 5 |
| Time window + TOTP/HOTP | 23–30 | Defense Validation | Lab 5 |
| TOTP phishing/replay (AiTM) | 30 | Practical Attack | H19 (session replay) |
| MFA (chaining factors) | 32–36 | Defense Validation | — |
| MFA fatigue / push bombing | 36 | Optional / Mentioned Only | — |
| Passkeys / FIDO2 / WebAuthn | 39–43 | Defense Validation | Lab 5 |
| Session hijacking (stolen cookie) | 12 | Practical Attack | H19 |

## Lecture 6 — Recap (Kahoot)

> This lecture is a **Kahoot recap** (review questions), not new content. It reinforces: STRIDE-per-element, Least Privilege, Separation of Duties, Fail-Safe Defaults, Session hijacking, SCA, Complete Mediation, Open Design. All covered above.

---

## Parts that need a visual review from you (image-only slides)

These slide areas are images; I read most of the important ones but they need your confirmation they match:

- **Lecture 2:** slides 6–12 (SDLC diagrams), slide 14 (DREAD scoring detail), slides 15–23 (Software Security Principles). I read slide 11 (STRIDE), 24 (AuthN/AuthZ), 25–28 (Non-repudiation).
- **Lecture 3:** slides 5–6, 12 (principle diagrams). I read 3 (Least Privilege), 4 (Common Mechanism), 10 (Psychological Acceptability).
- **Lecture 1:** slides 15–17 (CIA diagram). I read 20–21 (OWASP Top 10).

> I did not guess the content of any slide I could not read. If a topic lives only in those images, tell me the page and I will add it.

---

## Bottom line: what counts as a real attack

**Practical Attacks for the project** = the ones with Labs (1, 2, 3) + the ones explained as a clear attack (session replay, offline password cracking, behavioral replay). Everything else is **Defense Validation**, a **Principle**, or **Optional**.
