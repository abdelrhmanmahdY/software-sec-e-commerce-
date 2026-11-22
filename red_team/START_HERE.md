# START HERE — SecureShop Red Team

This file tells you, in plain language: what's actually been done, what's still
open, and exactly which command to run next. If you've never done a pentest
before, read this top to bottom before touching anything else in `red_team/`.

## 1. What "done" actually means here

Every status below was produced by *running something and reading the output*,
not by assuming. Where something could **not** be run in a given environment,
that is stated honestly rather than guessed at.

| Area | Status | How you know |
|---|---|---|
| Bandit (Python SAST) | **Done, re-verified** | Re-run fresh in this session: 5 LOW findings, all manually read and confirmed non-exploitable (test code, a `DEBUG`-only fallback key, and a field being cleared to `""`). See `reports/static_analysis_report.md` / `bandit_results.json`. |
| Dependency scan (pip-audit) | **Done, re-verified** | Re-run fresh: 14 of 64 pinned packages carry known advisories (Django, Pillow, DRF, PyJWT, gunicorn, cryptography, etc. are behind current patched releases). See `reports/findings/RT-001-vulnerable-dependencies.md` and `reports/pip_audit.json`. |
| Naive Shop attacks (V1–V7) | **Done, re-verified live** | The naive shop (`naive_shop/app.py`) was actually started and actually attacked in this session — not copied from an old report. All 7 vulnerabilities reproduced. See `evidence/naive_shop/attack_results.md`. |
| SecureShop live regression (H5, H6, H9, H13, H19, H22) | **Done earlier, not re-verified in this session** | `evidence/live/regression_results.md` shows all 6 defenses held, from the last live Docker run (2026-11-22). This environment has no Docker and no browser, so it could not be re-run here. **Re-run it yourself** before you submit — see §3. |
| Coupon reuse (H4), workflow bypass (H1/H2/H17), exceptional input (H7/H8) | **Not re-tested this round** | The matrix now says `NOT TESTED` honestly instead of guessing. The defensive code exists (read and confirmed), but only a live run earns a "DEFENSE HELD" status. |
| TOTP / MFA enforcement | **Not tested** | The feature exists in code but isn't enforced on seeded accounts. Confirm the intended policy with the Blue Team, then test it. |
| Reports (HTML + PDF) | **Done, rebuilt and visually checked** | All 11 reports regenerated and rendered to images to check for layout bugs. One real bug was found and fixed (an invisible white-on-white title on every cover page caused by a missing CSS override) — see `reports/build_reports.py`. |

**The one-line honest summary:** the static analysis and the naive-shop comparison are fully done and verified. The SecureShop live-app regression is well-prepared and was genuinely run once (2026-11-22), but needs to be re-run in an environment with Docker and a browser before you can call it final — don't present it as freshly verified without doing that.

## 2. Folder map

```
red_team/
├── START_HERE.md          <- you are here
├── RUN_GUIDE.md            <- step-by-step commands, explained
├── docker-compose.override.yml   <- fixes the Blue Team's CRLF script bugs without editing their files
├── reports/
│   ├── index.html          <- open this first for a clickable report index
│   ├── html/*.html          <- styled reports
│   ├── pdf/*.pdf             <- same reports as PDF
│   ├── findings/              <- one file per confirmed vulnerability
│   └── *.md                    <- source markdown for everything above
├── evidence/
│   ├── naive_shop/attack_results.md   <- fresh, re-run this session
│   └── live/*.md                       <- from the last live Docker run
├── live_tests/               <- the actual test scripts (run these, don't just read the reports)
└── labs/, secureshop_tests/   <- earlier prep work (hypotheses, test case docs)
```

## 3. What to do next (in order)

1. Open `reports/index.html` in a browser and skim the Executive Summary.
2. Get Docker running (see `RUN_GUIDE.md` §1) and bring SecureShop up.
3. Re-run `live_tests/run_regression.py` against the live app — this re-verifies
   H5/H6/H9/H13/H19/H22 for real, right before submission.
4. Re-run `live_tests/attack_naive.py` against the naive shop if you want to see
   it again (it's quick, pure stdlib, no Docker needed).
5. Re-run Bandit and pip-audit if the code changed since this report:
   `bandit -r . -x ./.venv,./.git,./red_team,./naive_shop -f json -o red_team/reports/bandit_results.json`
   `pip-audit -r requirements.txt --format json -o red_team/reports/pip_audit.json`
6. Rebuild the reports: `python red_team/reports/build_reports.py`, then re-export
   PDFs (see `RUN_GUIDE.md` §4).
7. Fill in the still-`NOT TESTED` rows of `reports/coverage_matrix.md` as you test
   them — don't mark anything "secure" without a live result.

## 4. Ground rules this work followed (carried over from the project PDF)

- Only the team's own local `SecureShop` was touched. Nothing external.
- No Blue Team source file was edited. Where their setup scripts had bugs
  (Windows line endings breaking the Linux container), the fix was an
  override file in `red_team/`, not an edit to their script.
- A `200 OK` or `403 Forbidden` was never treated as the finding by itself —
  every result above was checked against the actual data returned, the
  database state, or the account's permissions.
