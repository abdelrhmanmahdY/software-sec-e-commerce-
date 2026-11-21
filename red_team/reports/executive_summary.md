# Executive Summary — SecureShop Red Team Assessment

**Date:** 2026-11-22 · **Tester:** Red Team (sole member) · **Target:** SecureShop, local authorized build (`https://localhost`).

## Scope
A browser/HTTP-level security assessment of the team's own SecureShop application, plus an isolated intentionally-vulnerable "Naive Shop" built for comparison, and a Bandit static scan. All testing was local and authorized; no external systems were touched.

## Headline result
The Blue Team's current build is **well hardened**. Every vulnerability from the earlier source-review baseline (H1–H23) was **re-tested against the running application and found fixed** — verified by checking the real security property (ownership, token state, business outcome), not status codes. The intentionally-vulnerable Naive Shop demonstrates the same attacks succeeding when those controls are absent.

## Results at a glance
| | Naive Shop | SecureShop (current build) |
|---|---|---|
| Client-controlled price | CONFIRMED VULNERABILITY | DEFENSE HELD (server price, read-only field) |
| Coupon reuse | CONFIRMED VULNERABILITY | DEFENSE HELD (unique per-user constraint) |
| IDOR on orders | CONFIRMED VULNERABILITY | DEFENSE HELD (owner-scoped queryset → 404) |
| Workflow bypass | CONFIRMED VULNERABILITY | DEFENSE HELD (atomic credit+stock) |
| No login lockout | CONFIRMED VULNERABILITY | DEFENSE HELD (429 after 5 fails) |
| Broken access control | CONFIRMED VULNERABILITY | DEFENSE HELD (role checks, admin gated) |
| Token replay after logout | n/a | DEFENSE HELD (JWT blacklist → 401) |
| Public API docs | n/a | DEFENSE HELD (403 without admin) |

**SecureShop confirmed vulnerabilities this round: 0.** (Baseline-stage findings are retained separately for history.)

## Static analysis
Bandit on the application code: **5 LOW / medium-confidence** issues, all reviewed as **non-exploitable** (test-string "passwords", a dev-only fallback key used only when `DEBUG=True`). No high/medium severity. Dependency audit (pip-audit) results are in the dependency report.

## Notable observations (not vulnerabilities)
- The app enforces HTTPS (HSTS-ready), secure cookies, CSRF, and a full `audit` logging trail.
- TOTP groundwork exists but is not enforced on the seeded accounts — worth confirming the intended MFA policy.
- The Blue Team's shell scripts use Windows (CRLF) line endings, which breaks `docker-entrypoint.sh` and the cert script on a Linux container. **Recommended fix:** add a `.gitattributes` with `*.sh text eol=lf`. (This is an operational/build issue, not a security flaw; the Red Team did not modify Blue Team files.)

## Conclusion
Against the current build, SecureShop defends every course-relevant attack that was tested. The assessment is an **initial regression**; it should be repeated on the final submission build, and the browser-driven manual pass completed once the local TLS certificate is trusted in the browser.
