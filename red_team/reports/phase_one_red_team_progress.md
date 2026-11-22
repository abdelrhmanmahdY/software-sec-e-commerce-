# CET431 Phase One — Red Team Progress and Exit Gate

**Updated:** 2026-11-22  
**Repository:** `D:\software-sec-e-commerce-`  
**Branch / HEAD:** `main` / `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`

## Summary

Phase One has produced a preserved Naive Shop V1–V7 HTTP transcript, executed the checked-in offline lab examples, expanded the course-topic matrix, collected current-checkout isolated request-client evidence, and prepared a Blue Team handoff. No SecureShop implementation or persistent database record was modified.

**Phase status: PARTIAL — handoff material is ready, but full live SecureShop/browser verification remains outstanding.** Do not interpret source observations, offline demos, or isolated test-client behavior as proof about the running HTTPS deployment.

## Completed

| Work item | Status | Evidence |
|---|---|---|
| Baseline of official requirements, repository, history, reports, and execution risks | Completed | [`master_project_baseline.md`](master_project_baseline.md) |
| Naive Shop V1–V7 reproduced on the local, in-memory demo | Completed for demonstrated scenarios | [`naive_attack_20261122T021321Z.md`](../evidence/naive_shop/naive_attack_20261122T021321Z.md) |
| Offline course Lab 1–5 examples run and classified as simulations | Completed for checked-in scripts | [`local_demo_results_20261122.md`](../evidence/course_labs/local_demo_results_20261122.md) |
| Course security topic mapping updated with historical vs current evidence distinctions | In progress; mapping is broad, not a final verified matrix | [`official_course_security_coverage.md`](official_course_security_coverage.md) |
| Historical SecureShop transaction evidence reviewed | Completed as historical evidence only | [`backend_results.json`](../evidence/review/backend_results.json) |
| Current-checkout registration and MFA paths tested with synthetic in-memory fixtures | Completed as Django request-client tests | [`phase1_inmemory_registration_mfa_20261122.md`](../evidence/review/phase1_inmemory_registration_mfa_20261122.md) |
| Attack evidence assessment and evidence index | Drafted | [`phase_one_attack_evidence.md`](phase_one_attack_evidence.md); [`evidence_index.md`](evidence_index.md) |
| Blue Team handoff findings prepared | Drafted; requires owner acknowledgment | [`blue_team_security_handoff.md`](blue_team_security_handoff.md) |

## Confirmed findings / blockers

1. Password-only JWT login currently issues an access token to a TOTP-enabled synthetic account and that token accesses a protected API. Confirmed by current-checkout in-memory test; see RT-BT-01 handoff.
2. The `/signup/` HTML route creates an active account before email confirmation, while the dashboard and API registration paths create inactive accounts. Confirmed by current-checkout in-memory test; see RT-BT-02 handoff.
3. The recent bcrypt hasher change remains unverified in a fresh runtime because the local environment lacks the dependency and the running container is stale. See RT-BT-03.
4. Existing historical PostgreSQL regression evidence includes an INCONCLUSIVE direct-order workflow and cannot substitute for current live retesting.

## Not completed / requires coordination

- Browser-based end-to-end SecureShop testing against the current running HTTPS service, including customer/staff/admin role matrix and NewsletterSubscriber admin access.
- Safe database before/after verification for current SecureShop behavior. No persistent test-account actions were taken in this phase.
- Re-test of H4, H5, H9, H13, H22 and the other applicable coverage rows against a current, confirmed deployment.
- Full functional workflows: confirmation email use, catalog/search, cart persistence, newsletter/coupon, store-credit checkout, order history, profile editing, admin management, mobile layout, and invalid input/error handling.
- Final one-row-per-topic course coverage review with any slide/image-only topics resolved.
- Reconciliation of historical reports, exact report/page requirements, and visual evidence.

## Preservation and change scope

At the last Git inspection, `main` was at `6e33799b0b229aa8b97c3f0d3dbca9e7bc778bb5`. Existing worktree changes included the Red Team attack script, prior evidence, screenshots, and untracked reports; these were preserved. No Blue Team source/configuration file or persistent database record was changed in this phase. New artifacts are listed in [`evidence_index.md`](evidence_index.md).

## Recommended next steps

1. Blue Team owner acknowledges RT-BT-01/02 and RT-BT-03 and coordinates remediation; Red Team does not implement fixes.
2. Confirm a current deployment/build and an authorized disposable test account/data plan before touching persistent SecureShop data.
3. Run browser-based functional workflows and current SecureShop retests with request/response capture, screenshots, and database before/after snapshots; avoid consuming existing credit or altering existing users.
4. Update each matrix row only with results matching that exact build and test method.
5. After remediation, re-run the targeted retests and then prepare the final evidence, penetration, design, and demo deliverables.
