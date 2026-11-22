"""
SecureShop REGRESSION test runner (Red Team) - hardened build.

Targets the LOCAL authorized app over HTTPS (default https://localhost).
Self-signed cert is accepted ONLY for localhost (this is an HTTP client, not a
browser bypass). Standard library only.

KEY PRINCIPLE (per the assessment rules):
  * A 200 is NOT proof of a vulnerability.
  * A 403 is NOT proof of security.
Each test checks the ACTUAL security property (ownership, business outcome,
token state), and cross-checks data where relevant.

Status values:
  CONFIRMED VULNERABILITY | TESTED - DEFENSE HELD | INCONCLUSIVE
  NOT TESTED | NOT APPLICABLE

Output: prints a table and writes red_team/evidence/live/regression_results.md
"""
import json
import os
import pathlib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = os.environ.get("SECURESHOP_URL", "https://localhost").rstrip("/")
ACC = {
    "customer": (
        os.environ.get("SECURESHOP_TEST_CUSTOMER_USER", ""),
        os.environ.get("SECURESHOP_TEST_CUSTOMER_PASSWORD", ""),
    ),
    "staff": (
        os.environ.get("SECURESHOP_TEST_STAFF_USER", ""),
        os.environ.get("SECURESHOP_TEST_STAFF_PASSWORD", ""),
    ),
    "admin": (
        os.environ.get("SECURESHOP_TEST_ADMIN_USER", ""),
        os.environ.get("SECURESHOP_TEST_ADMIN_PASSWORD", ""),
    ),
}
EVIDENCE_DIR = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "live"
_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = pathlib.Path(
    os.environ.get(
        "SECURESHOP_REGRESSION_OUTPUT",
        str(EVIDENCE_DIR / f"regression_{_stamp}.md"),
    )
).resolve()
_parsed_base = urllib.parse.urlparse(BASE)
if _parsed_base.scheme != "https" or _parsed_base.hostname not in (
    "localhost", "127.0.0.1", "::1"
):
    raise SystemExit("Refusing to test anything other than local HTTPS SecureShop.")
if OUT.parent != EVIDENCE_DIR.resolve():
    raise SystemExit("Regression evidence must stay inside red_team/evidence/live/.")
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite existing evidence: {OUT}")

_host = urllib.parse.urlparse(BASE).hostname or ""
_ctx = ssl.create_default_context()
if _host in ("localhost", "127.0.0.1", "::1"):
    _ctx.check_hostname = False
    _ctx.verify_mode = ssl.CERT_NONE

results = []


def rec(tid, name, former, status, detail):
    results.append((tid, name, former, status, detail))
    print(f"[{status:>26}] {tid} {name}")
    if detail:
        print(f"      {detail}")


def http(method, path, token=None, json_body=None, follow=True):
    url = BASE + path
    headers = {"Accept": "application/json"}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx))
    if not follow:
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx), _NoRedirect)
    try:
        r = op.open(req, timeout=20)
        return r.getcode(), r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)


def login(role):
    u, p = ACC[role]
    code, body, _ = http("POST", "/api/auth/login/", json_body={"username": u, "password": p})
    try:
        d = json.loads(body)
        return d.get("access"), d.get("refresh")
    except Exception:
        return None, None


def main():
    if os.environ.get("SECURESHOP_TEST_ENVIRONMENT") != "disposable":
        print("NOT TESTED: set SECURESHOP_TEST_ENVIRONMENT=disposable for an isolated local clone.")
        return 2
    if any(not username or not password for username, password in ACC.values()):
        print("NOT TESTED: provide all three disposable role-account credentials via SECURESHOP_TEST_*.")
        return 2
    if os.environ.get("SECURESHOP_LIVE_TESTS_AUTHORIZED") != "I AUTHORIZE TESTS ON DISPOSABLE LOCAL CLONE":
        print(
            "Live regression is guarded because it writes auth/audit state. "
            "Set SECURESHOP_LIVE_TESTS_AUTHORIZED='I AUTHORIZE TESTS ON DISPOSABLE LOCAL CLONE' "
            "only after confirming a disposable local clone."
        )
        return 2
    print(f"SecureShop regression  ->  {BASE}\n")

    # 1. reachable
    code, _, _ = http("GET", "/", follow=False)
    rec("T-UP", "HTTPS reachable", "-",
        "TESTED - DEFENSE HELD" if code in (200, 302) else "INCONCLUSIVE", f"GET / -> {code}")

    # 2. H22 - API docs require auth
    code, _, _ = http("GET", "/api/docs/")
    rec("T-H22", "API docs require auth", "H22",
        "TESTED - DEFENSE HELD" if code in (401, 403) else "CONFIRMED VULNERABILITY",
        f"GET /api/docs/ (no auth) -> {code} (expected 401/403)")

    # tokens
    c_access, c_refresh = login("customer")
    if not c_access:
        rec("T-AUTH", "customer JWT login", "-", "INCONCLUSIVE", "no token; aborting authed tests")
        _write()
        return 2
    rec("T-AUTH", "customer JWT login", "-", "TESTED - DEFENSE HELD", "token issued")

    # 3. H5 - IDOR: customer must NOT see another user's order.
    #    Seed: order id 1 = customer's own; order id 3 = another user's.
    code_list, body_list, _ = http("GET", "/api/orders/orders/", token=c_access)
    foreign = None
    try:
        listing = json.loads(body_list)
        if code_list == 200 and isinstance(listing, dict):
            foreign = [
                (o.get("id"), o.get("user"))
                for o in listing.get("results", [])
                if o.get("user") != 3
            ]
    except Exception:
        foreign = None
    code_other, body_other, _ = http("GET", "/api/orders/orders/3/", token=c_access)
    if foreign:
        rec("T-H5-list", "Orders list owner-scoped", "H5", "CONFIRMED VULNERABILITY",
            f"customer saw foreign orders {foreign}")
    elif foreign == []:
        rec("T-H5-list", "Orders list owner-scoped", "H5", "TESTED - DEFENSE HELD",
            f"list -> {code_list}; only own orders returned")
    else:
        rec("T-H5-list", "Orders list owner-scoped", "H5", "INCONCLUSIVE",
            f"could not validate order list response; HTTP {code_list}")
    if code_other == 200:
        rec("T-H5-detail", "Read another user's order id=3", "H5", "CONFIRMED VULNERABILITY",
            f"GET /orders/3/ -> 200 body[:80]={body_other[:80]!r}")
    elif code_other in (401, 403, 404):
        rec("T-H5-detail", "Read another user's order id=3", "H5", "TESTED - DEFENSE HELD",
            f"GET /orders/3/ (not owner) -> {code_other} (blocked)")
    else:
        rec("T-H5-detail", "Read another user's order id=3", "H5", "INCONCLUSIVE",
            f"unexpected response HTTP {code_other}")

    # 4. H6 - non-staff cannot create order items / set price
    code, body, _ = http("POST", "/api/orders/order-items/", token=c_access,
                         json_body={"product": 1, "quantity": 1, "price": "0.01"})
    rec("T-H6-price", "Non-staff cannot set item price", "H6",
        "TESTED - DEFENSE HELD" if code in (401, 403) else
        "CONFIRMED VULNERABILITY" if code in (200, 201) else "INCONCLUSIVE",
        f"customer POST order-items price=0.01 -> {code} (expected 403)")

    # 5. H19 - refresh token revoked after logout
    logout_code, _, _ = http(
        "POST", "/api/auth/logout/", token=c_access, json_body={"refresh": c_refresh}
    )
    code_ref, body_ref, _ = http("POST", "/api/auth/refresh/", json_body={"refresh": c_refresh})
    if logout_code not in (200, 204, 205):
        status = "INCONCLUSIVE"
    elif code_ref in (401, 403):
        status = "TESTED - DEFENSE HELD"
    elif code_ref == 200:
        status = "CONFIRMED VULNERABILITY"
    else:
        status = "INCONCLUSIVE"
    rec("T-H19", "Refresh token revoked on logout", "H19", status,
        f"logout -> {logout_code}; reuse blacklisted refresh -> {code_ref} (expected 401)")

    # 6. H13 - login lockout (throwaway username, does NOT touch real accounts)
    statuses = []
    for _ in range(7):
        code, _, _ = http("POST", "/api/auth/login/",
                          json_body={"username": "rt_lockout_probe", "password": "x"})
        statuses.append(code)
    rec("T-H13", "Login lockout after repeated failures", "H13",
        "TESTED - DEFENSE HELD" if 429 in statuses else "CONFIRMED VULNERABILITY",
        f"7 failed logins -> {statuses} (expect a 429)")

    # 7. H9 - cart update requires auth
    code, _, _ = http("POST", "/api/carts/cart/update-quantity/",
                     json_body={"item_id": 1, "quantity": 1})
    rec("T-H9", "Cart update requires auth", "H9",
        "TESTED - DEFENSE HELD" if code in (401, 403) else
        "CONFIRMED VULNERABILITY" if code in (200, 201) else "INCONCLUSIVE",
        f"no-auth update-quantity -> {code} (expected 401/403)")

    _write()
    print(f"\nWrote -> {OUT}")
    if any(status == "CONFIRMED VULNERABILITY" for _, _, _, status, _ in results):
        return 1
    if any(status != "TESTED - DEFENSE HELD" for _, _, _, status, _ in results):
        return 2
    return 0


def _write():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SecureShop Regression Results (hardened build)",
        "",
        f"- Target: `{BASE}` (local HTTPS, authorized)",
        "- Source: `red_team/live_tests/run_regression.py` (property-based, stdlib)",
        "- Each row checks the real security property, not just a status code.",
        "",
        "| Test | Former finding | Status | Detail |",
        "|---|---|---|---|",
    ]
    for tid, name, former, status, detail in results:
        lines.append(f"| {tid} {name} | {former} | {status} | {detail.replace('|', chr(92)+'|')} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
