# CET431 Official Requirements Compliance Dashboard

**Audit date:** 2026-11-22  
**Application:** SecureShop, `https://localhost`  
**Grade status:** No final grade is invented. Evidence is insufficient for a reliable numeric score.

## Completion summary

| Area | Approximate completion | Basis |
|---|---:|---|
| Functional requirements | 25% | Desktop login/shop/admin observed; most core workflows not end-to-end verified |
| Security requirements | 35% | Mixed: source/unit evidence exists, but many course topics remain live-unverified |
| Documentation | 55% | README, threat model and reports exist; design report/complete evidence remain gaps |
| Testing and evidence | 45% | 16 tests passed; live database/browser evidence exists; many screenshots/requests absent |
| Demo readiness | 40% | Working admin/customer flows exist, but demo sequence lacks complete cart/checkout and naive comparison |

## Critical prioritization

1. Complete and document registration/confirmation, cart mutation, newsletter issuance, checkout and order history browser workflows.
2. Prove coupon reuse, workflow state and client-side price checks against live database state.
3. Replace or qualify report claims that are currently placeholders or code-only.

## High prioritization

1. Live-retest login lockout and JWT refresh blacklist.
2. Re-run SQLi, XSS and CSRF checks safely and retain raw responses/screenshots.
3. Complete mobile and invalid-input evidence.
4. Add a standalone 8–12 page Security Design Report.
5. Restore/verify Git history.

## Medium prioritization

1. Fix or document shop/dashboard clock element JavaScript console errors.
2. Improve report evidence index and browser screenshot naming.
3. Complete 10–15 minute demo rehearsal and Q&A notes.

## Core live findings

- Customer session: shop loaded; direct Django newsletter URL returned login/authorization treatment, no subscriber data for that state.
- Staff: Django dashboard loaded; direct newsletter URL returned HTTP 403 with no subscriber data.
- Admin: Django newsletter URL loaded and displayed 6 live subscribers, plus add/change/delete controls.
- Unauthenticated: Django newsletter URL redirected to Django admin login.
- Live database: PostgreSQL 16, all migrations applied, 5 users, 6 newsletter subscribers, 4 products, 2 orders.
- Automated tests: 16/16 passed.

## Recommended next action

Approve a second evidence-gathering phase focused on functional workflows and live security retests. Do not modify Blue Team code or database records until that evidence pass is complete.
