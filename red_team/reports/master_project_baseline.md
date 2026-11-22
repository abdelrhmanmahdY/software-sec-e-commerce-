# CET431 Master Project Baseline

**Review date:** 2026-11-22  
**Repository:** `D:\software-sec-e-commerce-`  
**Branch / HEAD:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`  
**Official specification:** `C:\Users\jun69\Desktop\CET431_Project_Description.pdf` (3 pages)  
**Course materials:** `C:\Users\jun69\Desktop\sec lec and labs\` (Lectures 1–6, Labs 1–5)  
**Scope:** Phase Zero read-only baseline. No SecureShop source, database rows, or existing reports/evidence were changed while preparing this baseline.

## 1. Repository identity and preservation status

- The local `main` branch tracks `origin/main` at the current HEAD. The latest commit is **“Apply bcrypt password hashing changes”**; the immediately preceding commit is **“Restore files from previous commit”** (`6dc3f28`).
- Git status at inspection:
  - One tracked modification: `red_team/evidence/naive_shop/attack_results.md`.
  - Existing untracked evidence/reports include Naive Shop screenshots, later Phase-B screenshots, and several audit reports.
  - No tracked Blue Team source or configuration changes were present in the worktree.
- These pre-existing changes are preserved. Attribution for untracked artifacts cannot be established from Git status alone; do not overwrite or clean them.
- `.env` and local certificate files are ignored by Git. Their contents were not read or copied into this report.
- The recorded prior baseline used `6dc3f282...`; this checkout is newer. Reports that state a different commit or missing files must be treated as historical unless re-verified.

## 2. Official requirements extracted

The official three-page PDF requires a working e-commerce site, protections for course-taught attacks, self-testing and Red-Team/Blue-Team testing, documentation, and a 10–15 minute demo with individual Q&A.

| Area | Requirement / points |
|---|---|
| Functional application | Registration/confirmation/login/logout (5); catalogue/details/search (4); session cart (4); coupons/newsletter (3); store-credit checkout/orders (5); profile and own orders (3); admin management of users/products/coupons (4); desktop/mobile usability and helpful errors (2). Total: 30. |
| Security | Demonstrate each applicable course attack against a naive implementation and show it fails against SecureShop; apply controls across relevant features; test unexpected inputs/sequences; maintain a one-row-per-topic coverage matrix linking scenario, root cause, defense, code location, and evidence. Total: 35. |
| Testing | Self-test every matrix row, retain evidence, and report Red-Team/Blue-Team findings including request, result, and severity. |
| Documentation | Git history, README with setup/test accounts/one-page architecture, an approximately 8–12-page Security Design Report with threat model and complete matrix, Attack Evidence Report, and Red Team Penetration Test Report. |
| Demo and grade | Live demo (10–15 minutes) and each team member answers for their contribution. Grading also assigns 5 points to code quality/architecture and 10 to demo/Q&A; the PDF specifies a six-member team. |

Course sources were found in the supplied folder: six lecture PDFs and five lab PDFs. The repository has extracted lecture/lab checklists and local lab walkthroughs. The checklist itself notes image-only slides that need visual review, so it is not sufficient evidence that every slide topic has been mapped.

## 3. Current project map

| Component | Location | Baseline responsibility |
|---|---|---|
| SecureShop | `users/`, `products/`, `carts/`, `orders/`, `dashboard/`, `audit/`, `config/` | Django/DRF application; server-rendered customer/admin pages; authentication, business logic, and audit records. |
| Naive Shop | `naive_shop/app.py` | Isolated Python standard-library HTTP demo bound in source to `127.0.0.1:8010`, with in-memory seed data and deliberate V1–V7 weaknesses. It is a lab demonstration, not a second full e-commerce UI. |
| Red Team | `red_team/labs/`, `live_tests/`, `secureshop_tests/`, `evidence/`, `reports/` | Course walkthroughs, local attack demos, SecureShop test cases, evidence, and reports. |
| Infrastructure | `Dockerfile`, `docker-compose.yml`, `red_team/docker-compose.override.yml`, `nginx/default.conf`, `scripts/` | Django/Gunicorn, PostgreSQL, nginx TLS termination, local certificates, and Compose overrides. |
| Documentation | root `README.md`, `docs/`, `red_team/README.md`, `red_team/reports/` | Setup, architecture, TLS/AAA, course mapping, and assessment output. |

The Django tests are concentrated in `audit/tests.py`. The `users/`, `dashboard/`, `products/`, `carts/`, and `orders/` test modules are currently placeholders. Existing audit tests cover authentication/lockout, authorization, price/status handling, and audit logging; source presence is not equivalent to full functional coverage.

## 4. Existing work and evidence status

| Item | Observed state | Evidence limit |
|---|---|---|
| V1–V7 Naive Shop | App and attack script exist. `evidence/naive_shop/attack_results.md` records all seven as confirmed, with run timestamp `2026-11-22T01:50:31Z`. | The retained file is a summary, not a complete raw HTTP transcript. The test script currently resets in-memory data and writes to that same evidence file; do not rerun it without preserving output to a new path. |
| Naive Shop screenshots | Home and open-admin screenshots exist. | They establish page appearance/state, not full raw request/response evidence. |
| SecureShop regression | `evidence/live/regression_results.md` records local HTTPS tests for H22, H5, H6, H19, H13, H9, and reachability. | H13 is explicitly **INCONCLUSIVE**: its recorded sequence was seven `429` responses, not the expected initial failures followed by lockout. Some other entries establish only an HTTP status, not the security/business property. The evidence is from before the latest HEAD and is not a retest of that commit. |
| Prior baseline findings | `evidence/live/baseline_results.md` records historical H4/H13 concerns and inconclusive H5/H8 states. | Historical baseline is not evidence about the current HEAD. |
| Course demos/tests | Five lab folders, local demo scripts, endpoint map, hypotheses, and individual SecureShop test-case documents exist. | Several lecture/lab topics have only a walkthrough or source-level claim; they need a justified status and evidence, not a name-only matrix row. |
| Functional evidence | Phase-B screenshots and a pre-test database dump exist. The functional matrix remains mostly PARTIAL or NOT TESTED. | Screenshots do not provide full HTTP/database before-after evidence. The earlier workflow left persistent test artifacts; do not reset or reverse database state without approval. |

The running Compose project was observed with PostgreSQL healthy and web/nginx containers running. The app's HTTP/browser behavior was not retested during Phase Zero. No Naive Shop listener was present on port 8010 at inspection.

## 5. Contradictions and stale claims

1. `red_team/reports/red_team_final_deliverables_checklist.md` says Naive Shop and its attack script/evidence are missing. They exist in this checkout, and Git history includes the restore commit. The checklist is stale.
2. `red_team/evidence/README.md` says evidence is empty, while evidence files are present.
3. `red_team/reports/documentation_compliance_matrix.md` says Git was unavailable. Git was available through the GitHub Desktop installation; branch, HEAD, status, and history were inspected.
4. `red_team/README.md` describes SecureShop testing as not yet executed, while later reports/evidence describe live regression. It is not a reliable current-status entry point without reconciliation.
5. `red_team/reports/naive_vs_secureshop_comparison.md` and the penetration report state broad SecureShop defenses as verified. This is stronger than the underlying retained evidence for some rows; H13 is expressly inconclusive, and status-only checks do not prove the control's reason or business outcome.
6. Several reports describe password storage as PBKDF2. Current `config/settings.py` selects a custom bcrypt-SHA256/pepper hasher; the latest commit changed this. The Docker app currently running reports PBKDF2, showing that the running container does not reflect the latest source.
7. The custom hasher cannot generate a password hash in the repository `.venv` because the `bcrypt` module is absent there; `requirements.txt` does not pin `bcrypt`. The current container's configured hasher is still PBKDF2, so container success does not validate the new code. This is a release-blocking verification gap, not yet a tested failure of the current production-style image.
8. The Naive Shop comparison is suitable for its seven security demonstrations, but its minimal pages are not a full e-commerce UI. The official functional UI requirement applies to SecureShop; do not expand Naive Shop solely for appearance unless the instructor requires it.

## 6. Documentation and deliverable inventory

| Deliverable | Current location/state |
|---|---|
| Root README/setup/architecture | `README.md` exists; claims and credential guidance need reconciliation with the latest bcrypt change and current operation. |
| Red Team README/setup | `red_team/README.md`, `START_HERE.md`, and `RUN_GUIDE.md` exist but contradict one another in status language. |
| Threat model | `red_team/reports/threat_model.md` exists; needs validation against current code and tests. |
| Coverage matrix | `red_team/reports/coverage_matrix.md` and `security_compliance_matrix.md` overlap; neither is a demonstrated complete one-row-per-course-topic final matrix. |
| Attack Evidence Report | `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md` exists but contains screenshot placeholders and claims beyond its raw evidence. |
| Penetration Test Report | `red_team/reports/red_team_penetration_test_report.md` exists, but its “completed” claims conflict with test evidence; `pentest_report_template.md` is also present. |
| Naive/Secure comparison | `red_team/reports/naive_vs_secureshop_comparison.md` exists; portions need current evidence and more conservative statuses. |
| Security Design Report (8–12 pages) | No clearly named standalone report was found. Existing architecture/TLS/threat documents do not establish that the required report is complete. |
| Evidence index | No authoritative evidence inventory was found. `red_team/evidence/README.md` is a template/instruction document, not an index. |
| Demo runbook | No timed executable runbook was found. `demo_readiness.md` is not a substitute. |
| Final audit | Multiple earlier audits exist, including stale/untracked files. Preserve them; identify one future authoritative report rather than silently replacing history. |

## 7. Risks and dependencies

- The source HEAD changed only minutes before inspection. The bcrypt dependency/configuration issue touches the same recent shared security change; do not edit those Blue Team files until the teammate change is confirmed stable or the owner approves a targeted fix.
- The live Docker image is stale relative to HEAD. Do not treat its PBKDF2 behavior or its earlier regression tests as proof for the latest source.
- Database and app volumes persist. Avoid seed reset, checkout, coupon redemption, user deletion, or other state-changing workflows without a dedicated account, backup, and approval where the action may affect existing data.
- Existing attack scripts write evidence files. New executions must use new, dated output files and retain request/response and state proof.
- The self-signed HTTPS certificate may require browser confirmation. Only the local project host is authorized.
- The six-person rubric cannot be mapped to Git authors without a team roster; multiple aliases may represent the same person. Do not claim every member has meaningful commits based on author counts alone.

## 8. Required phase plan

1. **Phase Zero — baseline (this report):** requirements, repository, history, reports/evidence, infrastructure, tests, contradictions, risks.
2. **Phase One — Red Team:** preserve existing artifacts; improve dated raw evidence capture; safely rerun local Naive V1–V7; review all lecture/lab topics; finish the topic matrix, attack evidence, pentest report, demo instructions, and handoff gate. Do not alter SecureShop.
3. **Phase Two — handoff and Blue Team:** provide a defense-by-defense handoff. Before any SecureShop edit, check current Git status and teammate conflicts. Resolve the bcrypt dependency/configuration issue with its owner; verify fresh-container behavior and add focused tests. Make only approved, minimal fixes.
4. **Phase Three — regression:** after Blue changes, retest the same attacks on local SecureShop with disposable roles and protected data; verify actual business/database outcomes and legitimate workflows.
5. **Phase Four — final documentation:** reconcile README, standalone Security Design Report, evidence index, Attack Evidence Report, penetration report, comparison, and timed demo runbook against actual results.
6. **Phase Five — final audit:** read-only rubric audit, stale-report labeling without deleting history, link/evidence validation, secret scan without printing secret values, and an honest readiness decision.

**Phase Zero conclusion:** The project has substantial code, lab preparation, Naive Shop demonstrations, and reports, but it is not yet verified submission-ready. Continue with Phase One; keep the recently changed bcrypt files untouched until the ownership/conflict question is resolved.
