"""
Naive Shop - INTENTIONALLY INSECURE educational e-commerce app.

Purpose: demonstrate how the CET431 course attacks SUCCEED when the standard
security controls are missing. It is the "naive implementation" half of the
required naive-vs-secure comparison. SecureShop is the secure half.

!!! DO NOT DEPLOY. LOCALHOST ONLY. Contains deliberate vulnerabilities. !!!

- Standard library only (http.server). No framework, no dependencies.
- In-memory data, reset with GET /reset.
- Runs on http://127.0.0.1:8010  (different port from SecureShop).
- Isolated: never touches SecureShop's code or database.

Run:   python naive_shop/app.py
Then open http://127.0.0.1:8010/ in a browser.

Deliberate vulnerabilities (each maps to a course topic / SecureShop defense):
  V1 Client-controlled price      -> /api/checkout trusts the client "price"
  V2 Coupon reuse / stacking      -> /api/apply_coupon has no per-user tracking
  V3 IDOR                         -> /api/orders/<id> returns ANY user's order
  V4 Workflow bypass             -> /api/confirm completes an order without payment
  V5 Client-controlled identity   -> the "user" cookie is trusted, no password
  V6 No login throttling          -> /api/login never locks out
  V7 Broken access control        -> /admin is open to everyone
"""
import html
import json
import re
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8010


def seed():
    return {
        "users": {
            "alice": {"id": 1, "password": "alice123", "role": "customer", "credit": 100},
            "bob":   {"id": 2, "password": "bob123",   "role": "customer", "credit": 100},
            "admin": {"id": 9, "password": "admin123", "role": "admin",    "credit": 0},
        },
        "products": {1: {"name": "Leather jacket", "price": 1337.0},
                     2: {"name": "Desk lamp", "price": 34.99}},
        "coupons": {"SAVE10": 10, "SAVE20": 20},
        "orders": {},            # id -> {owner, items, total, paid}
        "order_seq": 0,
    }


DB = seed()


def page(title, body):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:system-ui;margin:2rem;max-width:720px}}
.warn{{background:#fee;border:1px solid #c00;padding:.6rem;border-radius:6px;color:#900}}
code{{background:#eef;padding:.1rem .3rem}}</style></head><body>
<div class="warn"><b>NAIVE SHOP</b> - intentionally insecure demo. Localhost only.</div>
<h2>{title}</h2>{body}</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ---- helpers ----
    def _send(self, code, body, ctype="text/html; charset=utf-8", cookie=None):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def _current_user(self):
        # V5: identity comes straight from a client-controlled cookie. No check.
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return c["user"].value if "user" in c else None

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    # ---- routing ----
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            items = "".join(
                f"<li>#{pid} {p['name']} - ${p['price']:.2f}</li>"
                for pid, p in DB["products"].items())
            who = self._current_user() or "(not logged in)"
            return self._send(200, page("Home", f"""
<p>Logged in as: <b>{html.escape(who)}</b></p>
<ul>{items}</ul>
<p>Test accounts: alice/alice123, bob/bob123, admin/admin123</p>
<p>API: POST /api/login, /api/checkout, /api/apply_coupon;
GET /api/orders/&lt;id&gt;, /api/confirm?order=ID, /admin, /reset</p>"""))

        if self.path == "/reset":
            DB.clear()
            DB.update(seed())
            return self._json(200, {"ok": True, "message": "data reset"})

        # V7: /admin open to anyone, no access control.
        if self.path == "/admin":
            rows = "".join(f"<tr><td>{u}</td><td>{d['role']}</td><td>${d['credit']}</td></tr>"
                           for u, d in DB["users"].items())
            return self._send(200, page("Admin (unprotected!)",
                f"<table border=1><tr><th>user</th><th>role</th><th>credit</th></tr>{rows}</table>"))

        # V3: IDOR - returns any order regardless of who asks.
        m = re.fullmatch(r"/api/orders/(\d+)", self.path)
        if m:
            oid = int(m.group(1))
            order = DB["orders"].get(oid)
            if not order:
                return self._json(404, {"error": "no such order"})
            return self._json(200, order)   # no ownership check!

        # V4: workflow bypass - confirm completes an order without payment.
        m = re.fullmatch(r"/api/confirm\?order=(\d+)", self.path)
        if m:
            oid = int(m.group(1))
            order = DB["orders"].get(oid)
            if not order:
                return self._json(404, {"error": "no such order"})
            order["paid"] = True             # never checks payment!
            return self._json(200, {"confirmed": True, "order": order})

        return self._json(404, {"error": "not found"})

    def do_POST(self):
        body = self._body()

        # V6: login never throttles; V5: sets a trusted identity cookie.
        if self.path == "/api/login":
            u = DB["users"].get(body.get("username", ""))
            if u and u["password"] == body.get("password"):
                # identity handed to the client, trusted back unchanged
                return self._send(200, json.dumps({"ok": True}),
                                  "application/json", cookie=f"user={body['username']}; Path=/")
            return self._json(401, {"error": "bad credentials"})   # no attempt counter

        # V1: checkout trusts the client-supplied price.
        if self.path == "/api/checkout":
            user = self._current_user()
            if not user:
                return self._json(401, {"error": "login first"})
            pid = int(body.get("product_id", 0))
            client_price = float(body.get("price", 0))   # <-- trusts the client
            DB["order_seq"] += 1
            oid = DB["order_seq"]
            DB["orders"][oid] = {"id": oid, "owner": user, "product_id": pid,
                                 "total": client_price, "paid": False}
            return self._json(200, {"order_id": oid, "charged": client_price})

        # V2: coupon applied with no per-user tracking -> reuse / stacking.
        if self.path == "/api/apply_coupon":
            code = str(body.get("code", "")).upper()
            base = float(body.get("subtotal", 0))
            pct = DB["coupons"].get(code)
            if pct is None:
                return self._json(400, {"error": "invalid coupon"})
            # no check whether this user already used it; can be applied repeatedly
            return self._json(200, {"discount_percent": pct,
                                    "new_subtotal": round(base * (1 - pct / 100), 2)})

        return self._json(404, {"error": "not found"})


if __name__ == "__main__":
    print(f"Naive Shop (INSECURE) running at http://{HOST}:{PORT}/  -  Ctrl+C to stop")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
