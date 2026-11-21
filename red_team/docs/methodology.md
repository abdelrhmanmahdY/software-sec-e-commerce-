# Red Team Methodology

This file explains **how** we work: the tools, how we rate the severity of any finding (DREAD), and the "naive vs secure" approach.

---

## 1. Tools (course-only)

| Tool | Reference | Used for |
|---|---|---|
| **Burp Suite Community** (Proxy, Repeater, Intruder, Site map) | Lab 1 | Intercept, edit, and replay HTTP requests |
| **FoxyProxy** + Burp CA cert | Lab 1 | Route browser traffic through Burp |
| **Python `requests`** scripts | Lab 3 | Automate simple tests |
| **Browser DevTools** | general | Read requests, cookies, and JS |

> We do not add tools just because they are popular. We use what the course taught.

### Short Burp workflow

1. Start Burp, enable the Proxy listener on `127.0.0.1:8080`.
2. Point the browser at Burp via FoxyProxy, and install the Burp CA cert for HTTPS.
3. Browse the site normally — Burp records everything in **HTTP history** and **Site map**.
4. Found an interesting request? `Ctrl+R` → **Repeater** (edit and resend by hand), or `Ctrl+I` → **Intruder** (try many values automatically).
5. Watch the difference in **Status Code** and **Response Length** — that is what reveals the flaw.

| Status | Meaning for the attacker (from Lab 1) |
|---|---|
| 200 OK | Endpoint is live, inspect the body |
| 400 | Validation exists, try tweaking the payload |
| 401/403 | Protected — try an access-control bypass |
| 302 | Redirect — in Lab 3 this was the brute-force success signal |
| 500 | The input broke the backend — possible injection or logic flaw |

---

## 2. Severity rating: DREAD

The course taught **DREAD** (Lecture 2, slides 13–14) to prioritize threats after STRIDE. We use it to compute a justified severity for each finding.

Each factor is 1 to 3, and the sum determines the level:

| Factor | Question |
|---|---|
| **D**amage | If exploited, how much damage? |
| **R**eproducibility | How easily does it reproduce? |
| **E**xploitability | How much effort/skill is needed? |
| **A**ffected users | Who and how many are affected? |
| **D**iscoverability | How easily is it discovered? |

**Score:** sum of the five factors (5–15).

| Sum | Level |
|---|---|
| 12–15 | **Critical / High** |
| 9–11 | **Medium** |
| 5–8 | **Low** |

> Every severity in the reports is **estimated** until the attack is actually confirmed against the Blue version.

### Example calculation (Hypothesis H1 — checkout without payment check)
D=3, R=3, E=2, A=2, D=2 → sum 12 → **High (estimated, UNVERIFIED)**.

---

## 3. Naive vs Secure approach

The PDF (item 3) requires: "the attack **works against a naive implementation and fails against their own**."

For each practical topic we prepare 3 things:

1. **Naive:** the weak code (smallest isolated example that shows the flaw, or the PortSwigger lab itself).
2. **Attack:** the steps that break the naive version.
3. **Secure:** the change that blocks the same attack, and why it blocks it.

> **Practical decision:** we do not build a full vulnerable application. We use:
> - The original PortSwigger labs as the naive implementation (evidence via your screenshots).
> - + a small local Python example per topic (a naive function next to a secure function) so the explanation is clear and independent of any network.

---

## 4. From a Lab to a SecureShop test case

Each walkthrough ends with a **reusable test case** — the same Lab attack idea, phrased as steps to run against a SecureShop endpoint later. The test cases are collected in `secureshop_tests/test_cases/`.

Lifecycle:
```
Lab (learned) → Test case (prepared) → [testing window] → Finding (confirmed) → Blue Team fix
```
