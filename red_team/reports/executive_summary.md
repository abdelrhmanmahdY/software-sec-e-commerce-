# Executive Summary — Current Red Team Assessment

**Date:** 2026-11-22 · **Target:** local SecureShop source and isolated tests; loopback-only Naive Shop.

> This summary supersedes earlier reports that claimed all SecureShop attacks were blocked or that live HTTPS testing was current. No Docker service, shared PostgreSQL database, or live SecureShop HTTPS target was started in this assessment.

## Result

Naive Shop is presentation-ready and all seven intended attacks reproduced against `127.0.0.1:8010`. SecureShop evidence is limited to disposable SQLite `:memory:` tests and the Django suite (16/16 passed). These verify several controls but also expose open findings:

- Password-only JWT issuance for an account with TOTP enabled; the token accessed a protected orders endpoint.
- HTML `/signup/` creates an active account before email confirmation.
- Clean migrations do not create `audit_auththrottle`; the TOTP verification endpoint errors before its lockout policy can run.
- Cart add requested with quantity 3 returned quantity 4 and allowed a cart quantity above stock; checkout later rejected it without changing stock, credit, or order count.
- pip-audit found 216 advisories across 14 packages in 64 declared dependencies. Exploitability was not assessed.

## Verified controls (isolated test scope only)

The in-memory tests observed coupon replay rejection, stock rejection without transaction-state changes, forged cookie denial, unauthenticated admin/docs denial, CSRF rejection, refresh-token blacklist behavior, IDOR/RBAC controls, password lockout, and audit-log tests. See [security_compliance_matrix.md](security_compliance_matrix.md) for precise environments and limits.

## Static analysis and final assessment

Bandit application-source scan: two LOW / MEDIUM-confidence observations; no medium/high findings. pip-audit advisories are an open dependency hygiene finding. The assessment is **NOT production readiness evidence**. Live TLS, headers, SQLi/XSS, PostgreSQL races, full workflow-bypass retest, and browser behavior remain NOT TESTED.
