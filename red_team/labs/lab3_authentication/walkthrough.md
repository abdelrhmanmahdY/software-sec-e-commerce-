# Lab 3 — Authentication (2FA broken logic)

**Course reference:** Lab 3.1 (all slides) + Lecture 4 (slides 9–15, 20) + Lecture 5 (slide 34).
**Type:** Practical Attack.
**Status:** Walkthrough ready (DEMO). Real PortSwigger run needs a manual step from you.

This lab combines three attack ideas the course teaches:
1. **Client-controlled identity** — the server trusts a username sitting in a cookie.
2. **Brute force** — the 4-digit 2FA code has no rate limit.
3. **Automation** — a Python `requests` script drives it.

---

## 1. The vulnerability (plain)

After a correct password, the app asks for a 4-digit code emailed to the user. But the server decides *whose* code to generate from a cookie `verify=<username>` that the client fully controls. Change it to `verify=carlos` and the server issues and checks Carlos's code — and the 4-digit code has no attempt limit, so all 10,000 values can be tried.

## 2. Objective

Reach Carlos's account without knowing his password.

## 3. Attack, step by step (`wiener : peter`)

1. Log in as wiener and walk through 2FA. In `POST /login2`, note the `verify` parameter/cookie naming the account.
2. Log out to reset the flow.
3. In Repeater, send `GET /login2` with the cookie edited to `verify=carlos`. The server silently generates a 2FA code for Carlos (still `200 OK`).
4. Log in again as yourself, submit a deliberately wrong code to cleanly re-open the second step.
5. Send `POST /login2` to **Intruder**. Keep `verify=carlos` fixed; mark `mfa-code` as the payload position; brute-force `0000`–`9999`.
6. Wrong guesses return `200` with the same page; the correct one returns `302` to `/my-account` — that's the signal.
7. Load that response in the browser → logged in as Carlos. Lab solved.

## 4. The four key requests (illustrative — not real evidence)

| # | Request | Why it matters |
|---|---|---|
| 1 | `POST /login` (wiener) | Response sets `Set-Cookie: verify=wiener` — identity handed to the client |
| 2 | `GET /login2` | Carries `Cookie: verify=wiener`, nothing else proves who's asking |
| 3 | `GET /login2` (edited to `verify=carlos`) | Server generates Carlos's code, no extra check |
| 4 | `POST /login2` with `mfa-code` (brute) | Wrong = 200, correct = 302 Found |

> The course's Python script (Lab 3, CODE 1/12–12/12) automates this **against the PortSwigger lab only**. We do **not** point any such script at SecureShop or any other host.

## 5. Root cause

Identity is stored client-side (a plain username cookie) and trusted back unchanged, instead of being tracked server-side in the session. Plus no rate-limit/lockout on the code (Lecture 4 slide 20).

## 6. Defense

- Track the authenticated identity **server-side** in the session after the password step; ignore any client-supplied `verify` field.
- Bind the 2FA code to that server-side identity.
- Rate-limit and lock out after a few failed code attempts.
- Return one generic error, and don't leak which factor failed (Lecture 5 slide 34).
- Demo: `auth_identity_demo.py`.

## 7. Run the local demo

```powershell
python red_team/labs/lab3_authentication/auth_identity_demo.py
```
It simulates (in memory, no network) the verify-cookie trust flaw and a bounded brute-force counter, then shows the secure version blocking both.

## 8. Reusable SecureShop test cases

- [`tc_t5_auth.md`](../../secureshop_tests/test_cases/tc_t5_auth.md) — identity trust, login rate-limit, user enumeration, JWT after logout.
- Hypotheses **H11, H12, H13, H14, H19, H20**.

> **Safety note:** any brute-force style test against SecureShop must be a **small, bounded** number of attempts on a throwaway test account, on localhost, only during the agreed window. Never a full 10k sweep against a shared/graded instance.

## 9. Evidence to collect (manual), under `evidence/lab3/`
The `Set-Cookie: verify=` response, the edited `verify=carlos` request, the Intruder result table (302 at the winning code), and the solved banner.
