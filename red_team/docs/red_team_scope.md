# Red Team Scope — SecureShop

## 1. Who I am and what I own

I am the Red Team member responsible for the **entire** Red Team part of the project, alone:
- Reproducing and documenting every course-relevant Lab.
- Writing attack scenarios and test cases.
- Preparing evidence templates and the Red Team contribution to the Security Coverage Matrix.
- Writing the final Penetration Test Report.

## 2. Boundaries (very important)

Allowed:
- Work **inside `red_team/` only**.
- Read the rest of the repo as a read-only reference.
- Run isolated local examples using the Python standard library.
- Open authorized PortSwigger labs with my own account.

Not allowed:
- Modifying any file outside `red_team/` (backend, frontend, models, settings, tests, the main README).
- Any git commit / push / history or identity change.
- Adding any new dependency.
- **Any real attack against the SecureShop application now** — the application is under development.
- Testing any real site, university systems, or other students' machines.
- Fabricating results, screenshots, or requests/responses.

## 3. Ethics rules (PDF, item 8)

- "Attack **only** your own team's website, inside the course environment and within the agreed time window."
- "Never test real websites, other students' machines, or university systems without written permission."
- "Every member must be able to explain every line submitted."

⚠️ The repo's main README contains a public Railway URL (`alx-project-nexus-production...`). **It must never be touched.** All testing is local (`localhost`) against an agreed version.

## 4. What I must deliver (PDF, item 5)

| Deliverable | Our file |
|---|---|
| Red Team Penetration Test Report | `reports/pentest_report_template.md` |
| Contribution to the Attack Evidence Report | `evidence/` + `reports/coverage_matrix.md` |
| Contribution to the Security Coverage Matrix | `reports/coverage_matrix.md` |
| Documented findings (what was tried, request, result, severity) | `reports/findings_template.md` |

## 5. Timeline (PDF)

- **Week 9:** Phase 1 submission.
- **Week 10:** Phase 1 discussion (5 marks).
- **Week 14:** Phase 2 (15 marks): complete + Red Team testing + live demo.

Today is 2026-11-21. The actual testing window against the Blue version is not set yet — the team must agree on it.
