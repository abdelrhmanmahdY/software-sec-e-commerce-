# CET431 Red Team Final Deliverables Checklist

**Audit date:** 2026-11-22  
**Scope:** Red Team responsibility deliverables only  
**Audit boundary:** Read-only. No Blue Team code, data, configuration, or existing reports were modified.

## 1. Executive status

The Red Team workspace is only partially complete in the current checkout.

### Critical blockers

1. `naive_shop/app.py` is missing.
2. `red_team/live_tests/attack_naive.py` is missing.
3. No executed Naive Shop evidence file exists in the current checkout.
4. The main Red Team Penetration Test Report is missing as a completed report; only a template is present.
5. The Naive vs SecureShop comparison report is missing.
6. No standalone 8–12 page Security Design Report exists.
7. No evidence index exists.
8. No executable demo runbook exists.
9. No Red Team README or setup/entry-point document exists in the current checkout.
10. Threat-model report is missing in the current checkout even though a stale documentation matrix refers to it.

## 2. Naive Shop gap analysis

### Current status

The Naive Shop is **NOT IMPLEMENTED in the current checkout**. `naive_shop/app.py` does not exist, so V1–V7 cannot currently be run or reproduced.

The following files used in earlier reports are also absent:

- `naive_shop/app.py`
- `red_team/live_tests/attack_naive.py`
- `red_team/evidence/naive_shop/attack_results.md`
- `red_team/reports/naive_vs_secureshop_comparison.md`

The repository previously may have had these files, but they are not present now. Earlier report text is **documentation of an earlier state**, not current executable evidence.

### V1–V7 assessment

| Scenario | Vulnerable feature | Script execution | Result reproducibility | Impact evidence | Screenshot/raw proof | Overall |
|---|---|---|---|---|---|---|
| V1 client-controlled price | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V2 coupon reuse/stacking | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V3 order IDOR | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V4 unpaid workflow confirmation | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V5 client-controlled identity | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V6 no login throttling | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |
| V7 open admin | NOT IMPLEMENTED in current checkout | NOT TESTED | NOT TESTED | Not present | Not present | NOT TESTED |

The older `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` and baseline HTML mention V1–V7 and a Naive Shop, but the executable app and evidence are missing. Those claims must not be counted as current verification.

### Official UI sufficiency

Before rebuilding, the official UI requirement is not demonstrably met in the current checkout because no application exists to inspect. A future Naive Shop must include, at minimum:

- Registration/login
- Product catalogue/details/search/filter
- Cart add/remove/quantity
- Newsletter/coupon issuance and application
- Checkout and order history
- Profile
- Admin functionality appropriate to the lab
- Isolated loopback binding and disposable data

## 3. Complete course/topic mapping

The repository course checklist is `red_team/docs/lecture_checklist.md` and `red_team/docs/lab_checklist.md`.

| Course topic | Lab/test asset | Naive scenario | Attack script | Evidence | SecureShop retest | Report location |
|---|---|---|---|---|---|---|
| Excessive trust in client-side controls | Lab 1; `tc_t1_client_side_price.md`; `naive_price_demo.py` | V1 missing | Missing `attack_naive.py` V1 | Missing Naive evidence | Not independently rerun in current checkout | `red_team/reports/coverage_matrix.md` |
| Flawed coupon business rules | Lab 2.1; `tc_t2_coupon_rules.md`; `coupon_replay_demo.py` | V2 missing | Missing `attack_naive.py` V2 | Missing Naive evidence | H3/H4 in baseline; final live status not complete | `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` |
| Exceptional/invalid input | Lab 2.2; `tc_t3_exceptional_input.md`; `email_truncation_demo.py` | Not mapped to V1–V7 | Missing Naive scenario/script | No raw proof | No complete malformed-input pass | `red_team/reports/coverage_matrix.md` |
| Insufficient workflow validation | Lab 2.3; `tc_t4_workflow_validation.md`; `workflow_skip_demo.py` | V4 missing | Missing `attack_naive.py` V4 | Missing Naive evidence | Checkout browser success exists for disposable account; insufficient-credit rejection not independently documented | `red_team/reports/coverage_matrix.md` |
| Broken authentication identity | Lab 3.1; `tc_t5_auth.md`; `auth_identity_demo.py` | V5 missing | Missing `attack_naive.py` V5 | Missing Naive evidence | Not fully retested in current checkout | `red_team/reports/coverage_matrix.md` |
| Brute-force and login lockout | Lab 3/Lecture 4; `tc_t5_auth.md` | V6 missing | Missing `attack_naive.py` V6 | Baseline `baseline_results.md` has V/H13 summary | Baseline 401x6 exists; final 429 behavior not reproduced in current checkout | `red_team/evidence/live/baseline_results.md` |
| Authorization/RBAC/IDOR | Lectures 2–3; `tc_access_control.md` | V3/V7 missing | Missing `attack_naive.py` V3/V7 | H5 and role screenshots partly present | H5 historical proof exists; final browser/admin roles tested | `red_team/evidence/live/H5_idor_proof.md`; `red_team/evidence/browser/` |
| Least privilege | Lecture 3; `tc_access_control.md` | V7 missing | Missing `attack_naive.py` V7 | Browser customer/staff/admin screenshots | Customer, staff and admin newsletter states tested | `red_team/evidence/browser/phase-a-*newsletter-admin.png` |
| Separation of duties | Lectures 3/6; `tc_access_control.md` | Missing | Missing | No staff-escalation evidence | NOT TESTED | `red_team/secureshop_tests/hypotheses.md` H16 |
| Password storage | Lecture 4; `tc_t5_auth.md` | Not mapped | Missing | No hash-inspection proof | Source/config only | `red_team/reports/coverage_matrix.md` |
| Account lockout/rate limiting | Lecture 4; `tc_t5_auth.md` | V6 missing | Missing | Baseline 401x6 | Not independently rerun | `red_team/evidence/live/baseline_results.md` |
| Behavioral biometrics/anomaly detection | Lab 4; `tc_defense_behavioral.md`; anomaly demo | No Naive scenario | Demo script only | Demo evidence absent | No implementation found | `red_team/labs/lab4_anomaly_detection/` |
| Location-based authentication | Lab 5; `tc_defense_location_time_passkey.md`; defense demo | No Naive scenario | Demo script only | Demo evidence absent | No implementation found | `red_team/labs/lab5_location_time_passkey/` |
| Time window/TOTP/HOTP | Lab 5/Lecture 5; `tc_defense_location_time_passkey.md` | No Naive scenario | Defense demo only | TOTP no live browser evidence | Source fields/routes exist; enforcement not demonstrated | `red_team/labs/lab5_location_time_passkey/` |
| Passkeys/WebAuthn | Lab 5/Lecture 5; `tc_defense_location_time_passkey.md` | No Naive scenario | No SecureShop implementation test | No evidence | NOT IMPLEMENTED/NOT TESTED | `red_team/labs/lab5_location_time_passkey/` |
| Session hijacking/JWT replay | Lecture 5; `tc_t5_auth.md` | No matching V7 scenario | Missing | No raw final replay evidence in current checkout | NOT TESTED in current checkout | `red_team/reports/coverage_matrix.md` |
| MFA fatigue/push and biometrics FAR/FRR | Lecture 4/5 | No required implementation identified | Missing | No evidence | NOT APPLICABLE unless implemented | `red_team/docs/lecture_checklist.md` |
| Non-repudiation/audit logging | Lecture 2; `tc_access_control.md` | Missing | Missing | No dedicated evidence file | Source/live audit rows exist historically | `red_team/reports/coverage_matrix.md` |
| Fail secure/resiliency | Lecture 3; checkout/test cases | Missing | Missing | No complete failure-state evidence | Checkout business checks require live retest | `red_team/secureshop_tests/test_cases/` |
| Complete mediation | Lecture 3; `tc_access_control.md` | V7 | Missing | H9 baseline 403 summary | Cart quantity route mismatch found | `red_team/evidence/phase-b/06-cart-quantity-404.png` |
| Open design/security misconfiguration | Lectures 3/6; H22 | V7 is closest administrative exposure | Missing | H22 baseline summary plus admin browser screenshot | Not current final-build API/docs rerun | `red_team/evidence/live/baseline_results.md` |
| SQL injection | Optional injection topic | Missing | Missing | No raw executed test | NOT TESTED | `red_team/reports/coverage_matrix.md` |
| XSS | Optional injection topic | Missing | Missing | No raw executed test | NOT TESTED | `red_team/reports/coverage_matrix.md` |
| CSRF | Optional web security topic | Missing | Missing | No raw executed test | NOT TESTED | `red_team/reports/coverage_matrix.md` |
| TLS/transport security | Infrastructure/TLS topic | Not applicable | Missing | Browser HTTPS/admin screenshots | HTTPS live behavior observed | `docs/TLS_AAA.md` |
| Dependency/SCA | Supply-chain/security quality topic | Not applicable | No Naive scenario | No current pip-audit/Bandit report in checkout | NOT VERIFIED | `red_team/reports/` does not contain current scans |
| STRIDE/DREAD/threat modeling | Methodology | Not applicable | Missing | No threat-model report in current checkout | Documentation incomplete | `red_team/docs/methodology.md` |

## 4. Missing course topics

The repository checklist identifies these additional or not-complete areas:

- Exceptional input and over-long data.
- Full login/MFA broken-logic scenario.
- Behavioral anomaly replay.
- Impossible travel/location.
- Time-window/TOTP/HOTP and replay.
- Passkeys/WebAuthn.
- Password storage and offline cracking result.
- Session replay/JWT replay.
- Non-repudiation/audit completeness.
- Separation of duties/staff escalation.
- Fail-secure behavior.
- SQLi, XSS and CSRF live evidence.
- Dependency/SCA results.
- Complete threat model and DREAD evidence.

## 5. Evidence-quality classification

Classifications:

- `COMPLETE` — reproducible raw request/response and demonstrated impact.
- `PARTIAL` — screenshots or summaries exist but missing raw proof or DB/impact detail.
- `DOCUMENTATION ONLY` — summary or claim without sufficient raw evidence.
- `NOT TESTED` — no reproducible evidence.

| Evidence | Classification | Reason |
|---|---|---|
| H5 historical prose in `evidence/live/H5_idor_proof.md` | PARTIAL | It gives a response example and impact, but no raw request headers, exact timestamp or repeatable command/output bundle. |
| `evidence/live/baseline_results.md` | PARTIAL | Real status snippets exist, but several rows are inconclusive or HTTP-status-only. |
| `reports/live_baseline_report.md` | DOCUMENTATION ONLY for final baseline | It reports baseline tests but depends on older live evidence and is explicitly non-final. |
| `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` | DOCUMENTATION ONLY | It contains placeholder screenshot markers and broad claimed final results with no complete raw evidence files in the current checkout. |
| `red_team/evidence/browser/phase-a-*` | PARTIAL | Real screenshots prove page state, but do not contain raw request/response or database snapshots. |
| `red_team/evidence/phase-b/*` | PARTIAL | Real browser screenshots show workflows, but HTTP responses and database before/after logs are not bundled as raw text. |
| `red_team/evidence/phase-b/pre-phase-b.sql` | PARTIAL | Valid backup artifact, but it proves backup only, not a test outcome. |
| V1–V7 Naive evidence | NOT TESTED | No app, script or Naive evidence file exists in the current checkout. |
| H4 | PARTIAL/DOCUMENTATION ONLY | Baseline random/predictable coupon claim is present, but no current final random/duplicate test bundle. |
| H13 | PARTIAL | Baseline shows 401x6; no current raw 429/lockout proof. |
| H22 | PARTIAL | Baseline 200 is recorded; current browser role screenshots and 403 staff/unauth states exist historically. |
| H9 | PARTIAL | Baseline 403 exists; current browser quantity mismatch demonstrates a separate frontend failure. |
| 16-test suite claim | DOCUMENTATION ONLY in current evidence set | No current test log or report file is present; only report text claims it. |

## 6. Report-completeness audit

| Deliverable | Actual path | Status | Missing content |
|---|---|---|---|
| Security Coverage Matrix | `red_team/reports/coverage_matrix.md` | PARTIAL | Complete live-test rows, evidence links and final statuses |
| Security Coverage Matrix duplicate | `red_team/reports/security_compliance_matrix.md` | DUPLICATE/PARTIAL | Must reconcile or designate one canonical matrix |
| Threat Model | Missing | NOT IMPLEMENTED | Assets, trust boundaries, entry points, attackers and STRIDE mapping |
| Attack Evidence Report | `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` | DOCUMENTATION ONLY/PARTIAL | Raw requests, responses, screenshots and database deltas |
| Red Team Penetration Test Report | `red_team/reports/pentest_report_template.md` | TEMPLATE ONLY | All findings, scope, methodology, evidence and recommendations |
| Naive vs SecureShop Comparison | Missing | NOT IMPLEMENTED | V1–V7 or full course-topic comparison with links |
| Standalone Security Design Report | Missing | NOT IMPLEMENTED | 8–12 page design report |
| Evidence Index | Missing | NOT IMPLEMENTED | Inventory of every screenshot, log, request and database proof |
| Demo Runbook | `red_team/reports/demo_readiness.md` only | PARTIAL | Timed exact clicks, credentials handling, fallback and stop points |
| Red Team README/setup | Missing | NOT IMPLEMENTED | Start instructions, test scope, evidence commands and submission structure |
| README/main setup | Repository `README.md` | EXISTING/PARTIAL | Current Red Team responsibilities not part of main setup |
| Functional compliance matrix | `red_team/reports/functional_compliance_matrix.md` | PARTIAL | Complete browser/database evidence for every feature |
| Project architecture audit | `red_team/reports/full_project_architecture_audit.md` | COMPLETE as audit-only output | It is an audit report, not Red Team deliverable evidence |
| Red Team responsibility audit | `red_team/reports/red_team_responsibility_audit.md` | COMPLETE as audit-only output | It is contextual, not executable evidence |
| Live baseline | `red_team/reports/live_baseline_report.md` | PARTIAL | Mark as baseline only; no final regression status |
| Findings template | `red_team/reports/findings_template.md` | IMPLEMENTED TEMPLATE | Confirmed finding files are missing |

## 7. Duplicate and outdated reports

### Duplicate reports

- `red_team/reports/coverage_matrix.md`
- `red_team/reports/security_compliance_matrix.md`

### Outdated or inconsistent reports

- `red_team/reports/coverage_matrix.md` uses old NOT TESTED/Blue unfinished language.
- `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` claims final verification and 16/16 tests but omits raw current evidence.
- `red_team/reports/live_baseline_report.md` is clearly a baseline and must not be presented as final.
- `red_team/reports/pentest_report_template.md` is a template and must not be labeled a completed report.
- Documentation-compliance reports reference files that are missing in the current checkout.

## 8. Prioritized list of exactly what must be finished

### Critical

1. Restore or create the loopback-only Naive Shop and its V1–V7 attack script.
2. Execute V1–V7 and retain actual HTTP request/response and impact evidence.
3. Create the required Naive vs SecureShop comparison report.
4. Create the evidence index.
5. Complete the final Red Team Penetration Test Report.
6. Complete an 8–12 page Security Design Report.
7. Create an executable demo runbook.
8. Create Red Team README/setup instructions.

### High

1. Re-run H4/H5/H13/H22 and H9 independently against the current protected build.
2. Add disposable-account database snapshots before/after each test.
3. Complete coupon reuse, insufficient credit, store-credit, checkout and order-history evidence.
4. Complete exceptional-input, staff escalation, JWT/session replay and audit-log tests.
5. Add SQLi, XSS and CSRF live evidence or clearly mark them NOT TESTED.
6. Add TOTP/TOTP replay evidence or formally document absent/partial control.
7. Create the actual threat model report.
8. Consolidate the two overlapping security matrices into one canonical file.

### Medium

1. Add screenshots for each Naive and SecureShop comparison.
2. Add raw HTTP response files and database text evidence for browser workflows.
3. Complete behavioral-anomaly and Lab 5 defense demonstrations.
4. Add dependency and static-analysis reruns only if current source is available.
5. Verify Git history and include a meaningful-commit summary.
6. Rebuild HTML/PDF versions only after Markdown evidence is complete.

## 9. Submission-blocker determination

The project is **NOT READY for a complete Red Team submission** in the current checkout.

It has:

- course lab walkthroughs;
- SecureShop test-case definitions;
- isolated browser screenshots;
- initial baseline summaries;
- audit reports.

It lacks:

- the actual Naive Shop;
- executable Naive Shop attack evidence;
- complete raw evidence;
- completed final penetration report;
- standalone Security Design Report;
- evidence index;
- demo runbook;
- Naive vs SecureShop comparison;
- a current Red Team setup entry point.
