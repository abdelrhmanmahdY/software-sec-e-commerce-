# 10–15 Minute Demo and Q&A Readiness

## Readiness: PARTIAL

The project can demonstrate HTTPS login, role separation, the admin dashboard and Django newsletter access. The 10–15 minute demo is not yet complete evidence because core checkout, coupon, registration/confirmation, cart mutation and mobile workflows are not fully browser-verified.

## Proposed sequence

1. **Opening — 60 seconds:** show `https://localhost`, Docker containers, and the role distinction.
2. **Customer — 3 minutes:** login, show shop/products, open details, add/remove a cart item, open cart/profile and account history.
3. **Customer boundaries — 2 minutes:** navigate to `/admin/users/newslettersubscriber/` and show denial or login redirect.
4. **Staff — 2 minutes:** login, show staff dashboard, attempt protected Django admin newsletter URL and show 403.
5. **Admin — 2 minutes:** login, open Django admin and newsletter changelist; show six live subscriber rows and add/change/delete controls.
6. **Security evidence — 3 minutes:** show threat model, 16-test run, lockout/IDOR/unit evidence and honest unverified gaps.
7. **Naive vs Secure — 2 minutes:** show isolated lab scripts and explain that only verified controls count.
8. **Close — 1 minute:** summarize genuine findings, residual risk and next work.

## Role-specific questions to prepare

- Why does a customer get denied by Django admin?
- Why does staff get 403 while admin can view the newsletter changelist?
- Why is HTTP 403 not itself proof of no vulnerability?
- What does owner scoping mean in `OrderViewSet`?
- Why must checkout recompute price and total server-side?
- How does `CouponUsage` prevent reuse?
- How does the lockout backend track failures?
- Why can unit tests pass while browser evidence remains incomplete?
- How does the audit log prove/limit accountability?
- What is present for TOTP, and what is not enforced?
- Why are behavioral anomaly detection and passkeys not marked complete unless implemented?

## Q&A blockers

- Git history cannot currently be verified by the audit shell.
- Several security claims in reports need live reruns.
- No complete browser checkout/cart/registration evidence exists yet.
- Mobile behavior is not verified.

