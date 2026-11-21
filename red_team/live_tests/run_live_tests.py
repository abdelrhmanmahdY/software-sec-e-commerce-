"""
SecureShop LIVE baseline test runner (Red Team).

Runs SAFE, non-destructive checks against a LOCAL, authorized SecureShop
instance only (default http://127.0.0.1:8000). Records REAL results.

Rules enforced here:
  * localhost only (refuses non-local hosts unless SECURESHOP_ALLOW_REMOTE=1).
  * read-only / bounded checks only; no deletes, no credit-spending checkout.
  * standard library only (urllib) - runs on any Python, no pip install.

Status values (exactly as the project requires):
  CONFIRMED VULNERABILITY | TESTED - NOT VULNERABLE | NOT TESTED
  INCONCLUSIVE | BLOCKED

Output: prints a table and writes red_team/evidence/live/baseline_results.md.

IMPORTANT: This is an INITIAL BASELINE against an unfinished app. It is NOT a
final finding set. A suspicious code pattern is never a confirmed vulnerability
unless a check below actually demonstrates it.
"""
import http.cookiejar
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("SECURESHOP_URL", "http://127.0.0.1:8000").rstrip("/")
ACCOUNTS = {
    "customer": ("customer", "Customer!2026#Secure"),
    "staff": ("staff", "Staff!2026#Secure"),
}
OUT = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "live" / "baseline_results.md"

results = []  # list of dicts


def record(tid, name, hyp, status, detail):
    results.append({"id": tid, "name": name, "hyp": hyp, "status": status, "detail": detail})
    print(f"[{status:>24}] {tid}  {name}")
    if detail:
        print(f"      {detail}")


def _is_local(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return host in ("127.0.0.1", "localhost", "::1")


class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.jwt = None

    def req(self, method, path, body=None, json_body=None, headers=None, auth_jwt=False):
        url = BASE + path
        data = None
        hdrs = {"Accept": "application/json"}
        if json_body is not None:
            data = json.dumps(json_body).encode()
            hdrs["Content-Type"] = "application/json"
        elif body is not None:
            data = urllib.parse.urlencode(body).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        if auth_jwt and self.jwt:
            hdrs["Authorization"] = f"Bearer {self.jwt}"
        if headers:
            hdrs.update(headers)
        r = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            resp = self.opener.open(r, timeout=15)
            return resp.getcode(), resp.read().decode("utf-8", "replace"), dict(resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)

    def csrf(self, path="/dashboard/login/"):
        self.req("GET", path)
        for c in self.cj:
            if c.name == "csrftoken":
                return c.value
        return None


def main():
    print(f"SecureShop live baseline  ->  {BASE}\n")
    if not _is_local(BASE) and os.environ.get("SECURESHOP_ALLOW_REMOTE") != "1":
        print("REFUSED: target is not localhost. Set SECURESHOP_ALLOW_REMOTE=1 only")
        print("for an explicitly authorized host during an agreed testing window.")
        sys.exit(2)

    c = Client()

    # T-UP: server reachable
    try:
        code, _, _ = c.req("GET", "/")
        if code < 500:
            record("T-UP", "Server reachable", "-", "TESTED - NOT VULNERABLE",
                   f"GET / -> HTTP {code}")
        else:
            record("T-UP", "Server reachable", "-", "BLOCKED", f"GET / -> HTTP {code}")
    except Exception as e:
        record("T-UP", "Server reachable", "-", "BLOCKED",
               f"cannot reach {BASE}: {e}. Start the app, then rerun.")
        _write()
        print("\nServer not reachable - stopping. Start SecureShop and rerun.")
        return

    # T-AUTH: JWT login as customer
    code, body, _ = c.req("POST", "/api/auth/login/",
                          json_body={"username": ACCOUNTS["customer"][0],
                                     "password": ACCOUNTS["customer"][1]})
    try:
        c.jwt = json.loads(body).get("access")
    except Exception:
        c.jwt = None
    if c.jwt:
        record("T-AUTH", "JWT login (customer)", "-", "TESTED - NOT VULNERABLE",
               f"POST /api/auth/login/ -> HTTP {code}, got access token")
    else:
        record("T-AUTH", "JWT login (customer)", "-", "BLOCKED",
               f"POST /api/auth/login/ -> HTTP {code}; no token. Is seed_data run?")

    # T-SWAGGER (H22): public API schema
    code, _, _ = c.req("GET", "/api/docs/")
    record("T-SWAGGER", "API docs exposed without auth", "H22",
           "CONFIRMED VULNERABILITY" if code == 200 else "TESTED - NOT VULNERABLE",
           f"GET /api/docs/ (no auth) -> HTTP {code}")

    # T-UPDQTY-NOAUTH (H9/H8): unauthenticated access + error leakage
    code, body, _ = c.req("POST", "/api/carts/cart/update-quantity/",
                          json_body={"item_id": 999999, "quantity": 1})
    leaked = "error" in body.lower() and ("object" in body.lower() or "matching" in body.lower()
                                          or "traceback" in body.lower())
    if code in (401, 403):
        record("T-UPDQTY-NOAUTH", "update-quantity requires auth", "H9",
               "TESTED - NOT VULNERABLE", f"no-auth POST -> HTTP {code}")
    else:
        record("T-UPDQTY-NOAUTH", "update-quantity reachable without auth", "H9",
               "CONFIRMED VULNERABILITY" if code < 500 else "INCONCLUSIVE",
               f"no-auth POST -> HTTP {code}; body[:120]={body[:120]!r}")
    record("T-ERRLEAK", "Error body leaks internals", "H8",
           "CONFIRMED VULNERABILITY" if leaked else "INCONCLUSIVE",
           f"body[:160]={body[:160]!r}")

    # T-PROD-READ: product list readable (expected public read)
    code, _, _ = c.req("GET", "/api/products/products/")
    record("T-PROD-READ", "Product list readable", "-",
           "TESTED - NOT VULNERABLE", f"GET /api/products/products/ -> HTTP {code}")

    # T-ORDERS-SCOPE (H5): does customer see orders, and can they probe others' ids?
    if c.jwt:
        code, body, _ = c.req("GET", "/api/orders/orders/", auth_jwt=True)
        snippet = body[:200].replace("\n", " ")
        record("T-ORDERS-LIST", "Orders list scope (manual review)", "H5",
               "INCONCLUSIVE",
               f"GET /api/orders/orders/ -> HTTP {code}; needs a 2nd user's order to "
               f"confirm IDOR. body[:200]={snippet!r}")
        # Safe READ probe: try to fetch order id 1 (may belong to anyone)
        code1, body1, _ = c.req("GET", "/api/orders/orders/1/", auth_jwt=True)
        record("T-ORDERS-IDOR", "Read order id=1 as customer", "H5",
               "INCONCLUSIVE",
               f"GET /api/orders/orders/1/ -> HTTP {code1}; confirm ownership of id=1 "
               f"to classify (CONFIRMED if it belongs to another user).")
    else:
        record("T-ORDERS-LIST", "Orders list scope", "H5", "BLOCKED", "no JWT token")

    # T-RATELIMIT (H13): bounded wrong-password attempts (max 6)
    statuses = []
    for _ in range(6):
        code, _, _ = c.req("POST", "/api/auth/login/",
                           json_body={"username": ACCOUNTS["customer"][0],
                                      "password": "wrong-on-purpose"})
        statuses.append(code)
    locked = any(s == 429 for s in statuses) or statuses[-1] == 423
    record("T-RATELIMIT", "Login lockout / throttling (6 tries)", "H13",
           "TESTED - NOT VULNERABLE" if locked else "CONFIRMED VULNERABILITY",
           f"6 bad logins -> statuses {statuses}; "
           + ("throttled" if locked else "no lockout/throttle observed"))

    # T-NEWSLETTER (H4): predictable coupon codes
    token = c.csrf()
    if token:
        hdrs = {"X-CSRFToken": token, "Referer": BASE + "/"}
        codes = []
        for i in range(2):
            email = f"rt_probe_{i}@example.test"
            code, body, _ = c.req("POST", "/dashboard/newsletter/signup/",
                                  json_body={"email": email}, headers=hdrs)
            m = re.search(r'"coupon_code"\s*:\s*"([^"]+)"', body)
            if m:
                codes.append(m.group(1))
        if len(codes) >= 1:
            predictable = any(re.fullmatch(r"NEWS\d+", x or "") for x in codes)
            record("T-NEWSLETTER", "Newsletter coupon predictability", "H4",
                   "CONFIRMED VULNERABILITY" if predictable else "INCONCLUSIVE",
                   f"issued codes {codes}; pattern NEWS#### = predictable" if predictable
                   else f"issued codes {codes}")
        else:
            record("T-NEWSLETTER", "Newsletter coupon predictability", "H4",
                   "INCONCLUSIVE", "no coupon_code in response (endpoint may have changed)")
    else:
        record("T-NEWSLETTER", "Newsletter coupon predictability", "H4",
               "BLOCKED", "could not obtain CSRF token")

    # Checks that CHANGE important data / spend credit -> left for manual run
    for tid, name, hyp in [
        ("T-CHECKOUT-PAY", "Checkout without covering total", "H1"),
        ("T-CHECKOUT-FREE", "Free checkout endpoint", "H2"),
        ("T-COUPON-REUSE", "Coupon reuse across orders", "H3"),
        ("T-PRICE-TAMPER", "Client-set order item price", "H6"),
        ("T-STAFF-ESC", "Staff role escalation / delete", "H16"),
    ]:
        record(tid, name, hyp, "NOT TESTED",
               "changes data / spends credit / destructive - run manually on a "
               "recoverable DB during the agreed window (see test_cases/).")

    _write()
    print(f"\nWrote results -> {OUT}")


def _write():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SecureShop Live Baseline Results",
        "",
        f"- Target: `{BASE}` (local, authorized baseline)",
        "- Source: `red_team/live_tests/run_live_tests.py` (real HTTP, stdlib only)",
        "- Note: INITIAL BASELINE against an unfinished app. Not a final finding set.",
        "",
        "| Test | Hyp | Status | Detail |",
        "|---|---|---|---|",
    ]
    for r in results:
        d = r["detail"].replace("|", "\\|")
        lines.append(f"| {r['id']} {r['name']} | {r['hyp']} | {r['status']} | {d} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
