# CET431 Red Team — SecureShop

> **Current assessment status (2026-11-22):** Naive Shop V1–V7 passed on loopback. SecureShop was tested only with disposable in-memory SQLite fixtures and Django tests; live HTTPS/Docker/PostgreSQL testing is **NOT TESTED**. Open findings include password-only JWT issuance for TOTP-enabled users, an HTML signup route active before email confirmation, and a missing `AuthThrottle` migration. Do not treat older live-test summaries below as current evidence.

The current topic mapping is [security_compliance_matrix.md](reports/security_compliance_matrix.md); the authoritative final assessment is [FINAL_SECURITY_ASSESSMENT_REPORT.pdf](reports/FINAL_SECURITY_ASSESSMENT_REPORT.pdf).

This is the **Red Team** workspace for the SecureShop project. Everything here covers attack preparation, reproducing the course Labs, preparing test cases, and the reports.

> **Academic-integrity note:** This work is educational and local, against the team's own authorized SecureShop instance only (per the PDF, items 4 and 8).
>
> The sections below are historical preparation notes. For current results, use the status at the top of this file, the coverage matrix, and the final PDF.

---

## What's in this folder

| Folder | Contents |
|---|---|
| `docs/` | Scope, methodology (Burp + DREAD), and the Lab / Lecture checklists |
| `labs/` | **Track 1:** reproducing Labs 1–5 with isolated local examples + walkthroughs |
| `secureshop_tests/` | **Track 2:** endpoint map, the hypotheses (all Unverified), and ready-to-run test cases |
| `evidence/` | Place to store real evidence (screenshots, requests, outputs) after execution |
| `reports/` | The Coverage Matrix, plus the Findings and Pentest Report templates |

---

## Historical track plan (superseded)

- **Track 1 — Labs:** reproduce course material on isolated local examples.
- **Track 2 — SecureShop:** this is historical preparation status; see the current assessment and coverage matrix above.

---

## How to run the local examples

All `labs/` examples are written in Python **standard library** only — no `pip install`.

```powershell
# example
python red_team/labs/lab1_client_side_trust/naive_price_demo.py
```

Each example prints a comparison between a **naive implementation** (falls for the flaw) and a **secure implementation** (blocks it). No example connects to any network or site.

---

## Status labels used across all files

| Label | Meaning |
|---|---|
| `DEMO` | Result from a local educational example, not evidence about SecureShop |
| `UNVERIFIED` | Suspicion from reading the code, not yet confirmed by testing |
| `NOT TESTED` | Not yet attempted (waiting for the Blue version or a manual step from you) |
| `INCONCLUSIVE` | Tested but the result is not conclusive |
| `CONFIRMED` | Demonstrated in the stated authorized environment; historical/live scope must remain explicit |

---

## What needs a manual step from you (I cannot do these)

1. Opening PortSwigger Web Security Academy labs in Burp (needs a PortSwigger account + your browser). I prepared the steps in each walkthrough.
2. Taking the real Burp screenshots and saving them under `evidence/`.
3. Running the test cases against the Blue Team's final version during the testing window.

Details are in `reports/pentest_report_template.md` and at the end of each walkthrough.
