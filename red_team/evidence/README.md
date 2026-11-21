# Evidence

Real evidence from executed tests goes here. **Empty for now** — nothing has been tested against SecureShop.

## Folder layout (create a subfolder per topic when you run a test)

```
evidence/
├── lab1/                         # PortSwigger Lab 1 screenshots + requests
├── lab2/                         # PortSwigger Lab 2.1/2.2/2.3
├── lab3/                         # PortSwigger Lab 3.1
├── t1/  t2/  t3/  t4/  t5/        # SecureShop test-case evidence
├── access_control/
├── defense_behavioral/
└── defense_location_time_passkey/
```

## What to capture per item
- The exact HTTP request used (raw, from Burp or the script).
- The server response (status + relevant body).
- A screenshot when a UI state matters (e.g. "lab solved", order confirmation).
- A short caption: date, target (must be localhost or the authorized PortSwigger lab), and which test case / hypothesis it belongs to.

## Rules
- Never fabricate a screenshot, request, or response.
- Only capture from `localhost` or the authorized PortSwigger Academy lab — never a public/shared host.
- Name files clearly, e.g. `t1_tampered_price_request.png`, `t5_no_lockout_response.txt`.
