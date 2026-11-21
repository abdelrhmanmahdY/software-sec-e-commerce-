# Red Team Penetration Test Report — SecureShop

**Status: Initial regression assessment (completed).** Date: 2026-11-22. Target: SecureShop local authorized build, `https://localhost` (nginx + TLS). Tester: Red Team (sole member).

## 1. Executive summary
SecureShop's current build withstood every course-relevant attack that was tested. All earlier source-review hypotheses were re-tested against the running application and found **fixed**. One real finding remains: **outdated dependencies with known advisories** (patch hygiene). The Naive Shop confirms the same attacks succeed without these controls.

## 2. Scope & authorization
- **In scope:** local SecureShop (`https://localhost`) and the isolated `naive_shop/`.
- **Authorization:** own team project, local only, course environment (PDF items 4, 8).
- **Out of scope:** any public/Railway host, university systems, other machines.
- **Method:** HTTP client property-based tests + Django ORM DB checks + Bandit + pip-audit. Browser-pane manual pass pending local-cert trust.

## 3. Methodology
See `docs/methodology.md`. Each test verifies the real security property (ownership, token state, business outcome), never a bare status code. DREAD used for severity.

## 4. Threat model
See `threat_model.md` (STRIDE, assets, roles, trust boundaries).

## 5. Results — regression of former findings (all re-tested live)
| Former | Attack | Result | Evidence |
|---|---|---|---|
| H5 | IDOR on orders | **DEFENSE HELD** (non-owner → 404) | `evidence/live/regression_results.md` |
| H6 | Client-set price | **DEFENSE HELD** (403, read-only) | same |
| H1/H2 | Checkout bypass | **DEFENSE HELD** (credit+stock, atomic) | same |
| H3 | Coupon reuse | **DEFENSE HELD** (unique constraint) | DB check |
| H13 | Login lockout | **DEFENSE HELD** (429 after 5) | `regression_results.md` |
| H19 | Token replay after logout | **DEFENSE HELD** (blacklist → 401) | same |
| H9 | Unauth cart update | **DEFENSE HELD** (403) | same |
| H22 | Public API docs | **DEFENSE HELD** (403) | same |
| — | HTTP→HTTPS | **DEFENSE HELD** (301) | same |
| — | Admin URL exposure | **DEFENSE HELD** (login gate) | same |

**Confirmed SecureShop vulnerabilities (app logic): 0 this round.**

## 6. Findings
| ID | Title | Severity | Status |
|---|---|---|---|
| RT-001 | Vulnerable & outdated dependencies | Medium (est.) | CONFIRMED (SCA) — see `findings/RT-001-vulnerable-dependencies.md` |

Non-findings worth noting: MFA/TOTP present but not enforced on seed accounts; CRLF line endings break the Blue Team's shell scripts on Linux containers (build issue — recommend `.gitattributes *.sh text eol=lf`).

## 7. Static analysis
Bandit: 5 LOW, all non-exploitable. pip-audit: 15 packages with advisories (RT-001). See `static_analysis_report.md`.

## 8. Naive vs Secure
See `naive_vs_secureshop_comparison.md` — 7 attacks succeed on Naive Shop, all blocked on SecureShop, with executed evidence from both.

## 9. Recommendations (Blue Team)
1. **RT-001:** upgrade dependencies, re-run `pip-audit`, add SCA to CI.
2. Confirm the intended MFA/TOTP policy (enforce if required).
3. Fix shell-script line endings (`.gitattributes`).
4. Keep HSTS at a low max-age until TLS is finalized, then raise.

## 10. Limitations / not yet done
- Browser-driven manual exploration (screenshots) — blocked by the self-signed cert not being trusted in the browser pane; click "continue" in the pane to enable.
- Coupon/checkout happy-path abuse via the session UI (CSRF flow) — covered at the API/DB level here; a UI pass can follow.
- This is a **baseline regression**; repeat on the final submission build and record results separately.

## Appendix — reproduce
```
# 1. run SecureShop (Docker): see RUN_GUIDE.md  ->  https://localhost
# 2. regression:   python red_team/live_tests/run_regression.py
# 3. naive + attack:  python naive_shop/app.py  &&  python red_team/live_tests/attack_naive.py
# 4. static:   bandit ... ; pip-audit ...
```
