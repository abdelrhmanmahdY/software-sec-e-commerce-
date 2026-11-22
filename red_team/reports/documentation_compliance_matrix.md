# Documentation and Evidence Compliance Matrix

**Audit date:** 2026-11-22

| Required item | Status | Actual finding | Evidence / risk |
|---|---|---|---|
| README setup/accounts/architecture | PASS | README contains Docker setup, seed accounts, architecture, security summary and test commands. | `README.md` |
| Git repository and meaningful history | NOT TESTED / BLOCKED | Repository is present, but `git.exe` was unavailable to the audit shell. | Run/restore Git CLI before counting history as complete. |
| 8–12 page Security Design Report | PARTIAL | No clearly identified standalone 8–12 page design report was found. TLS/AAA and architecture reports exist but do not replace a complete design report. | `docs/TLS_AAA.md`, `red_team/reports/project_architecture.md` |
| Threat model with assets/entry points/attackers | PASS | STRIDE threat model exists and maps assets, roles, boundaries and entry points. | `red_team/reports/threat_model.md` |
| Complete Security Coverage Matrix | PARTIAL | Coverage matrix exists, but several entries say NOT TESTED or unverified. It is a useful matrix but not yet complete evidence coverage. | `red_team/reports/coverage_matrix.md` |
| Attack Evidence Report | PARTIAL | Attack evidence report exists, but many placeholders mark screenshots to insert. Live evidence folder now has some browser screenshots and regression files. | `docs/ATTACK_EVIDENCE_AND_PENTEST_REPORT.md`; `red_team/evidence/browser/` |
| Red Team Penetration Test Report | PARTIAL | Penetration report claims fixes and verification, but some rows are not independently reproduced and include evidence placeholders. | `red_team/reports/red_team_penetration_test_report.md` |
| Source code | PASS | Django source and test suite are present. | Repository root and app folders |
| Naive vs Secure comparison evidence | PARTIAL | Lab demos and naive attack scripts exist; browser/real-application comparison evidence is incomplete. | `red_team/labs/`, `red_team/evidence/naive_shop/attack_results.md` |
| Test suite and reproducible commands | PASS | 16 Django tests ran successfully against an isolated test database on 2026-11-22. | Live terminal output, `make test` equivalent command |
| Browser evidence | PARTIAL | Six browser role/admin/screenshots exist, but functional workflows beyond login/shop/admin are incomplete. | `red_team/evidence/browser/` |
| Live database evidence | PASS | Live PostgreSQL vendor and migration state confirmed; safe account/role and table counts recorded. | Docker shell output in this audit |

