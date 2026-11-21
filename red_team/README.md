# Red Team — SecureShop (CET431 Software Security)

This is the **Red Team** workspace for the SecureShop project. Everything here covers attack preparation, reproducing the course Labs, preparing test cases, and the reports.

> **Academic-integrity note:** This work is educational and local, against the team's own authorized SecureShop instance only (per the PDF, items 4 and 8).
>
> **Update (2026-11-22):** this note originally said no attack had been run yet. That's no longer true — see **`START_HERE.md`** for the current, accurate status: live regression tests have been run against SecureShop (`evidence/live/`), and the Naive Shop comparison attacks have been run and re-verified (`evidence/naive_shop/`). `START_HERE.md` is now the up-to-date entry point; read it before this file.

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

## The two tracks we work in

- **Track 1 — Labs (active now):** reproduce what each Lab taught, on an isolated local example or on the authorized PortSwigger environment. Fully educational.
- **Track 2 — SecureShop (prepared now, executed later):** test cases and scripts are ready, but we only run them against the Blue Team's final version during the testing window. Every hypothesis stays **Unverified**.

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
| `CONFIRMED` | Confirmed by an authorized real test (none so far) |

---

## What needs a manual step from you (I cannot do these)

1. Opening PortSwigger Web Security Academy labs in Burp (needs a PortSwigger account + your browser). I prepared the steps in each walkthrough.
2. Taking the real Burp screenshots and saving them under `evidence/`.
3. Running the test cases against the Blue Team's final version during the testing window.

Details are in `reports/pentest_report_template.md` and at the end of each walkthrough.
