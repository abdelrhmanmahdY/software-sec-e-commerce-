"""
Naive Shop - intentionally vulnerable CET431 teaching application.

The UI is a local-only presentation layer over the V1-V7 deliberately insecure
routes. All state is in memory and is reset by GET /reset.

DO NOT DEPLOY OR EXPOSE THIS APP TO A NETWORK.
"""
import html
import json
import re
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit


HOST, PORT = "127.0.0.1", 8010


def seed():
    return {
        "users": {
            "alice": {"id": 1, "password": "alice123", "role": "customer", "credit": 100},
            "bob": {"id": 2, "password": "bob123", "role": "customer", "credit": 100},
            "admin": {"id": 9, "password": "admin123", "role": "admin", "credit": 0},
        },
        "products": {
            1: {"name": "Leather Jacket", "price": 1337.0, "category": "Outerwear",
                "description": "A premium leather jacket with a deliberately tempting price."},
            2: {"name": "Desk Lamp", "price": 34.99, "category": "Home",
                "description": "A warm, adjustable desk lamp for focused study."},
            3: {"name": "Canvas Backpack", "price": 68.50, "category": "Accessories",
                "description": "A sturdy everyday bag with room for a laptop and notebooks."},
            4: {"name": "Wireless Headphones", "price": 119.00, "category": "Electronics",
                "description": "Comfortable over-ear headphones for work and travel."},
        },
        "coupons": {"SAVE10": 10, "SAVE20": 20},
        "orders": {},
        "order_seq": 0,
        "carts": {},
        "coupon_results": {},
    }


DB = seed()


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body, user=None, notice=""):
    account = (
        f'<a href="/profile">{esc(user)}</a> <a href="/logout">Sign out</a>'
        if user else '<a href="/login">Sign in</a>'
    )
    notice_html = f'<div class="notice">{esc(notice)}</div>' if notice else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#10172a">
<title>{esc(title)} | Naive Shop Lab</title>
<style>
:root{{--ink:#172033;--muted:#667085;--paper:#f5f7fb;--card:#fff;--line:#e4e9f1;
--brand:#5b55e7;--brand-dark:#3933b5;--accent:#f0a94b;--danger:#a42d38;--green:#167653}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
a{{color:inherit;text-decoration:none}}
button,input{{font:inherit}}
.top-note{{background:#351b22;color:#ffe4e4;text-align:center;padding:8px 14px;font-size:.84rem}}
.top-note strong{{letter-spacing:.08em}}
.header{{background:#10172a;color:#fff}}
.nav{{max-width:1180px;margin:auto;padding:17px 22px;display:flex;align-items:center;gap:26px}}
.brand{{font-weight:850;font-size:1.3rem;letter-spacing:-.04em;white-space:nowrap}}
.brand span{{color:#a7a4ff}}
.navlinks{{display:flex;align-items:center;gap:20px;margin-left:auto;color:#d4d8e6;font-size:.94rem}}
.navlinks a:hover{{color:#fff}}
.navright{{display:flex;align-items:center;gap:12px;white-space:nowrap}}
.navright a{{color:#fff}}
.pill{{border:1px solid #596078;border-radius:999px;padding:7px 12px;font-size:.86rem}}
.container{{width:min(1180px,100%);margin:0 auto;padding:28px 22px 60px}}
.hero{{display:grid;grid-template-columns:1.2fr .8fr;gap:30px;align-items:center;padding:36px 0 42px}}
.eyebrow{{font-size:.77rem;letter-spacing:.13em;text-transform:uppercase;color:var(--brand);font-weight:800}}
h1{{font-size:clamp(2rem,4vw,3.55rem);line-height:1.06;letter-spacing:-.055em;margin:10px 0 14px}}
h2{{font-size:1.75rem;line-height:1.15;letter-spacing:-.035em;margin:0 0 10px}}
h3{{margin:0 0 8px;line-height:1.25}}
p{{margin:0 0 14px}}
.muted{{color:var(--muted)}}
.hero-card{{min-height:250px;border-radius:24px;padding:28px;background:linear-gradient(145deg,#222947,#4b49a7);
color:#fff;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 18px 38px #24285a24}}
.hero-card .tag{{font-size:.82rem;color:#dadaff}}
.hero-card .price{{font-size:2.1rem;font-weight:800;letter-spacing:-.04em}}
.hero-card .price small{{font-size:.9rem;font-weight:500;opacity:.8}}
.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:15px;margin:12px 0 20px}}
.search{{display:flex;gap:8px;max-width:500px;width:100%}}
input,select{{border:1px solid #d6dce7;border-radius:10px;padding:11px 12px;background:#fff;color:var(--ink);min-width:0}}
input:focus,select:focus{{outline:3px solid #5b55e733;border-color:var(--brand)}}
.search input{{flex:1}}
.button{{display:inline-flex;justify-content:center;align-items:center;gap:7px;border:0;border-radius:10px;
padding:11px 16px;background:var(--brand);color:#fff;font-weight:750;cursor:pointer}}
.button:hover{{background:var(--brand-dark)}}
.button.secondary{{background:#ecebff;color:#3731ae}}
.button.ghost{{background:#fff;color:var(--ink);border:1px solid var(--line)}}
.button.danger{{background:#fff0f0;color:var(--danger);border:1px solid #f1d0d2}}
.button.small{{padding:8px 10px;font-size:.88rem}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:17px;overflow:hidden;
box-shadow:0 5px 16px #13213a08;display:flex;flex-direction:column}}
.product-art{{height:155px;display:grid;place-items:center;background:linear-gradient(135deg,#ebeaff,#d9e7fa);
color:#403bb0;font-size:3.1rem;font-weight:800;letter-spacing:-.08em}}
.product-art.alt1{{background:linear-gradient(135deg,#fff1dc,#f8d7b8);color:#994d21}}
.product-art.alt2{{background:linear-gradient(135deg,#e5f5ee,#c6e7d8);color:#226d54}}
.product-art.alt3{{background:linear-gradient(135deg,#f1e7fa,#decdf0);color:#7548a0}}
.card-body{{padding:16px;display:flex;flex-direction:column;flex:1}}
.category{{font-size:.75rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:750}}
.product-name{{font-size:1.1rem;margin:5px 0 6px}}
.card-body .muted{{font-size:.88rem;min-height:40px}}
.card-foot{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto;padding-top:12px}}
.price{{font-weight:850;font-size:1.1rem}}
.section-head{{display:flex;align-items:end;justify-content:space-between;gap:12px;margin:34px 0 15px}}
.panel{{background:#fff;border:1px solid var(--line);border-radius:17px;padding:20px;box-shadow:0 5px 16px #13213a08}}
.layout{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(270px,.7fr);gap:20px;align-items:start}}
.row{{display:flex;align-items:center;gap:12px}}
.spread{{display:flex;align-items:center;justify-content:space-between;gap:12px}}
.stack{{display:grid;gap:12px}}
.cart-row{{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:14px;align-items:center;
padding:14px 0;border-bottom:1px solid var(--line)}}
.qty{{width:92px}}
.form-grid{{display:grid;gap:13px}}
.form-grid label{{display:grid;gap:6px;font-size:.9rem;font-weight:700}}
.notice{{padding:12px 15px;border:1px solid #b5e3d2;background:#eaf8f1;color:#125b42;border-radius:11px;margin:12px 0 18px}}
.warning{{padding:12px 15px;border:1px solid #efc7a0;background:#fff4e8;color:#844514;border-radius:11px;margin:14px 0}}
.table-wrap{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:15px}}
table{{border-collapse:collapse;width:100%;min-width:560px}}
th,td{{text-align:left;padding:13px 15px;border-bottom:1px solid var(--line)}}
th{{background:#f8f9fc;color:#596274;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase}}
tr:last-child td{{border-bottom:0}}
.empty{{text-align:center;padding:40px 18px}}
.empty .icon{{font-size:2.4rem;margin-bottom:8px}}
.footer{{background:#10172a;color:#b9c0d0;padding:24px 20px;text-align:center;font-size:.86rem}}
.footer strong{{color:#fff}}
.demo-label{{display:inline-flex;border:1px solid #f0c891;border-radius:999px;padding:4px 9px;
background:#fff7eb;color:#754816;font-size:.74rem;font-weight:800;letter-spacing:.04em}}
.detail{{display:grid;grid-template-columns:.9fr 1.1fr;gap:26px;align-items:start}}
.detail .product-art{{height:340px;border-radius:20px;font-size:5rem}}
.notice-list{{padding-left:20px;color:var(--muted)}}
@media(max-width:850px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.nav{{gap:14px}}
.navlinks{{gap:12px}}.hero{{gap:18px}}}}
@media(max-width:640px){{.nav{{flex-wrap:wrap;padding:14px 16px;gap:12px}}
.navlinks{{order:3;overflow-x:auto;width:100%;margin:0;padding:4px 0 2px}}
.navright{{margin-left:auto}}.container{{padding:22px 16px 42px}}
.hero{{grid-template-columns:1fr;padding:20px 0 30px}}.hero-card{{min-height:200px}}
.grid{{grid-template-columns:1fr 1fr;gap:11px}}.product-art{{height:120px;font-size:2.5rem}}
.card-body{{padding:12px}}.card-foot{{align-items:flex-start;flex-direction:column}}
.layout,.detail{{grid-template-columns:1fr}}.detail .product-art{{height:240px}}
.toolbar{{align-items:stretch;flex-direction:column}}.cart-row{{grid-template-columns:1fr auto}}
.cart-row .row-actions{{grid-column:1/-1;justify-content:flex-end}}
h1{{font-size:2.4rem}}}}
@media(max-width:380px){{.grid{{grid-template-columns:1fr}}.navright{{gap:6px}}.pill{{padding:6px 9px}}}}
</style>
</head>
<body>
<div class="top-note"><strong>EDUCATIONAL LAB</strong> - Deliberately insecure. Localhost only. No real payments.</div>
<header class="header"><nav class="nav" aria-label="Main navigation">
<a class="brand" href="/">NAIVE<span>SHOP</span></a>
<div class="navlinks"><a href="/products">Shop</a><a href="/cart">Cart ({_cart_count(user)})</a>
<a href="/orders">Orders</a><a href="/profile">Account</a><a href="/admin">Admin</a></div>
<div class="navright">{account}</div>
</nav></header>
<main class="container">{notice_html}{body}</main>
<footer class="footer"><strong>Naive Shop Lab</strong> - CET431 local demonstration environment.
Intentionally vulnerable endpoints are labeled in the source.</footer>
</body></html>"""


def _cart_count(user):
    key = user or "guest"
    return sum(int(quantity) for quantity in DB["carts"].get(key, {}).values())


def _product_art(product_id):
    labels = {1: "LJ", 2: "DL", 3: "CB", 4: "WH"}
    styles = {1: "alt1", 2: "", 3: "alt2", 4: "alt3"}
    return f'<div class="product-art {styles.get(product_id, "")}">{labels.get(product_id, "NS")}</div>'


def _money(amount):
    try:
        return f"${float(amount):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _catalog_cards(products):
    cards = []
    for product_id, product in products:
        cards.append(f"""
<article class="card">
<a href="/product?id={product_id}" aria-label="View {esc(product['name'])}">
{_product_art(product_id)}</a>
<div class="card-body">
<div class="category">{esc(product['category'])}</div>
<h3 class="product-name"><a href="/product?id={product_id}">{esc(product['name'])}</a></h3>
<p class="muted">{esc(product['description'])}</p>
<div class="card-foot"><span class="price">{_money(product['price'])}</span>
<a class="button small" href="/product?id={product_id}">View item</a></div>
</div></article>""")
    return "\n".join(cards) or '<div class="panel empty">No products match your search.</div>'


def _login_form(message=""):
    warning = f'<div class="warning">{esc(message)}</div>' if message else ""
    return f"""
<section class="panel" style="max-width:520px;margin:22px auto">
<span class="eyebrow">Demo account</span><h2>Sign in</h2>
<p class="muted">Use one of the disposable accounts seeded in this local lab.</p>
{warning}
<form class="form-grid" action="/login" method="post">
<label>Username<input name="username" autocomplete="username" required></label>
<label>Password<input type="password" name="password" autocomplete="current-password" required></label>
<button class="button" type="submit">Sign in</button>
</form>
<p class="muted" style="margin-top:14px">Demo users: alice, bob, admin. Passwords are defined in the local app seed.</p>
<div class="warning"><b>Lab note:</b> the identity cookie is intentionally client-controlled (V5).</div>
</section>"""


def _cart_html(user):
    key = user or "guest"
    cart = DB["carts"].get(key, {})
    if not cart:
        return """
<div class="empty panel"><div class="icon">[ ]</div><h2>Your cart is empty</h2>
<p class="muted">Browse the collection and add an item to begin.</p>
<a class="button" href="/products">Explore products</a></div>"""

    rows = []
    subtotal = 0.0
    for product_id, quantity in cart.items():
        product = DB["products"].get(int(product_id))
        if not product:
            continue
        quantity = int(quantity)
        line_total = float(product["price"]) * quantity
        subtotal += line_total
        rows.append(f"""
<div class="cart-row">
<div><div class="category">{esc(product['category'])}</div><h3>{esc(product['name'])}</h3>
<span class="muted">{_money(product['price'])} each</span></div>
<form action="/cart/update" method="post" class="row"><input type="hidden" name="product_id" value="{int(product_id)}">
<input class="qty" type="number" name="quantity" value="{quantity}" min="1" aria-label="Quantity">
<button class="button secondary small" type="submit">Update</button></form>
<form class="row-actions" action="/cart/remove" method="post"><input type="hidden" name="product_id" value="{int(product_id)}">
<button class="button danger small" type="submit">Remove</button></form>
</div>""")

    coupon_result = DB["coupon_results"].get(key)
    coupon_html = ""
    if coupon_result:
        coupon_html = (
            f'<div class="notice">Coupon {esc(coupon_result["code"])} applied: '
            f'{int(coupon_result["discount_percent"])}% off; calculated total '
            f'{_money(coupon_result["new_subtotal"])}.</div>'
        )
    return f"""
<div class="section-head"><div><span class="eyebrow">Your selection</span><h2>Shopping cart</h2>
<p class="muted">Quantity and coupon calculations are handled by this demo server.</p></div>
<a class="button ghost" href="/products">Continue shopping</a></div>
<div class="layout"><section class="panel">{''.join(rows)}</section>
<aside class="panel stack"><h3>Order summary</h3><div class="spread"><span>Subtotal</span><b>{_money(subtotal)}</b></div>
{coupon_html}
<form action="/cart/coupon" method="post" class="form-grid"><label>Coupon code
<input name="code" placeholder="Try SAVE20" required></label>
<input type="hidden" name="subtotal" value="{subtotal:.2f}">
<button class="button secondary" type="submit">Apply coupon</button></form>
<a class="button" href="/checkout">Proceed to checkout</a>
<p class="muted">Coupons can be applied repeatedly in this intentionally vulnerable lab.</p></aside></div>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/html; charset=utf-8", cookie=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json; charset=utf-8")

    def _redirect(self, target, cookie=None):
        self.send_response(303)
        self.send_header("Location", target)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _current_user(self):
        # V5: this intentionally trusts a client-controlled identity cookie.
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        return cookies["user"].value if "user" in cookies else None

    def _body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    def _form(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        return {key: values[-1] for key, values in parse_qs(raw, keep_blank_values=True).items()}

    def _user_cart(self):
        key = self._current_user() or "guest"
        return key, DB["carts"].setdefault(key, {})

    def _create_order(self, username, product_id, client_price, quantity=1, items=None):
        DB["order_seq"] += 1
        order_id = DB["order_seq"]
        DB["orders"][order_id] = {
            "id": order_id,
            "owner": username,
            "product_id": product_id,
            "quantity": quantity,
            "items": items or [{"product_id": product_id, "quantity": quantity}],
            "total": client_price,
            "paid": False,
        }
        return order_id

    def _home(self, user):
        featured = DB["products"][1]
        account_action = (
            '<a class="button ghost" href="/profile">View account</a>'
            if user else '<a class="button ghost" href="/login">Sign in</a>'
        )
        body = f"""
<section class="hero"><div><span class="eyebrow">A local security lab</span>
<h1>Shop the demo.<br>Test the defenses.</h1>
<p class="muted">A presentation-friendly storefront for exploring what happens when
trust, authorization, and workflow checks are missing.</p>
<div class="row"><a class="button" href="/products">Browse products</a>
{account_action}</div>
<p style="margin-top:18px"><span class="demo-label">INTENTIONALLY VULNERABLE</span></p></div>
<aside class="hero-card"><span class="tag">FEATURED DEMO PRODUCT</span>
<div><h2>{esc(featured['name'])}</h2><p>{esc(featured['description'])}</p></div>
<div class="spread"><span>Catalog price</span><span class="price">{_money(featured['price'])}</span></div>
<a class="button" href="/product?id=1">View featured item</a></aside></section>
<section class="section-head"><div><span class="eyebrow">Curated for the demo</span>
<h2>Popular picks</h2><p class="muted">All products use disposable in-memory data.</p></div>
<a class="button ghost" href="/products">View all</a></section>
<div class="grid">{_catalog_cards(list(DB["products"].items())[:4])}</div>
<section class="warning" style="margin-top:28px"><b>Safe lab boundary:</b>
this app binds only to 127.0.0.1, stores data in memory, and never handles real payments.</section>"""
        return page("Home", body, user)

    def do_GET(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        user = self._current_user()

        if path == "/reset":
            # The attack harness uses this only against the local in-memory lab.
            DB.clear()
            DB.update(seed())
            return self._json(200, {"ok": True, "message": "data reset"})
        if path == "/" or path == "":
            return self._send(200, self._home(user))
        if path == "/products":
            term = query.get("q", [""])[0].strip()
            products = list(DB["products"].items())
            if term:
                products = [
                    pair for pair in products
                    if term.casefold() in pair[1]["name"].casefold()
                    or term.casefold() in pair[1]["category"].casefold()
                    or term.casefold() in pair[1]["description"].casefold()
                ]
            body = f"""
<div class="section-head"><div><span class="eyebrow">The collection</span><h2>Shop all products</h2>
<p class="muted">Search by name, category, or description.</p></div></div>
<div class="toolbar"><form class="search" action="/products" method="get">
<input name="q" value="{esc(term)}" placeholder="Search products..." aria-label="Search products">
<button class="button" type="submit">Search</button></form>
<span class="muted">{len(products)} item(s)</span></div>
<div class="grid">{_catalog_cards(products)}</div>"""
            return self._send(200, page("Products", body, user))
        if path == "/product":
            try:
                product_id = int(query.get("id", ["0"])[0])
                product = DB["products"][product_id]
            except (ValueError, KeyError):
                return self._send(404, page("Not found", '<div class="panel empty"><h2>Product not found</h2><a class="button" href="/products">Back to shop</a></div>', user))
            body = f"""
<div class="detail"><div>{_product_art(product_id)}</div><section>
<span class="eyebrow">{esc(product['category'])}</span><h1>{esc(product['name'])}</h1>
<p class="muted">{esc(product['description'])}</p><p class="price" style="font-size:1.7rem">{_money(product['price'])}</p>
<p class="demo-label">DEMO CATALOG PRICE - CLIENT PRICE IS TRUSTED AT CHECKOUT</p>
<form action="/cart/add" method="post" class="form-grid" style="max-width:340px;margin-top:18px">
<input type="hidden" name="product_id" value="{product_id}">
<label>Quantity<input name="quantity" type="number" value="1" min="1"></label>
<button class="button" type="submit">Add to cart</button></form>
<p style="margin-top:18px"><a class="muted" href="/products">Back to products</a></p></section></div>"""
            return self._send(200, page(product["name"], body, user))
        if path == "/login":
            return self._send(200, page("Sign in", _login_form(), user))
        if path == "/logout":
            return self._redirect("/", "user=; Path=/; Max-Age=0")
        if path == "/cart":
            notice = query.get("notice", [""])[0]
            return self._send(200, page("Cart", _cart_html(user), user, notice))
        if path == "/checkout":
            key = user or "guest"
            cart = DB["carts"].get(key, {})
            if not cart:
                return self._send(200, page("Checkout", _cart_html(user), user))
            items = [
                (int(product_id), int(quantity), DB["products"].get(int(product_id)))
                for product_id, quantity in cart.items()
            ]
            items = [item for item in items if item[2]]
            first_product_id = items[0][0]
            quantity = sum(item[1] for item in items)
            displayed_total = sum(float(product["price"]) * count for _, count, product in items)
            item_rows = "".join(
                f'<div class="spread"><span>{esc(product["name"])} x {count}</span>'
                f'<b>{_money(float(product["price"]) * count)}</b></div>'
                for _, count, product in items
            )
            body = f"""
<div class="section-head"><div><span class="eyebrow">Final step</span><h2>Checkout</h2>
<p class="muted">This is a no-payment teaching workflow.</p></div></div>
<div class="layout"><section class="panel"><h3>Delivery summary</h3>
{item_rows}<p class="muted">No address or payment details are collected.</p>
<div class="warning"><b>V1 demonstration:</b> the price field below is sent by the browser and trusted by the vulnerable endpoint.</div>
<form action="/checkout" method="post" class="form-grid">
<input type="hidden" name="product_id" value="{first_product_id}">
<input type="hidden" name="quantity" value="{quantity}">
<label>Client-submitted order total ($)<input name="price" type="number" step="0.01" value="{displayed_total:.2f}" required></label>
<button class="button" type="submit">Place demo order</button></form></section>
<aside class="panel stack"><h3>Summary</h3>{item_rows}
<div class="spread"><span>Catalog total</span><b>{_money(displayed_total)}</b></div>
<p class="muted">Vulnerable checkout accepts the submitted order total.</p></aside></div>"""
            return self._send(200, page("Checkout", body, user))
        if path == "/orders":
            if not user:
                body = f'<div class="panel empty"><h2>Sign in to view your orders</h2><a class="button" href="/login">Sign in</a></div>'
            else:
                orders = [order for order in DB["orders"].values() if order.get("owner") == user]
                order_rows = []
                for order in orders:
                    product = DB["products"].get(order["product_id"], {})
                    status = "PAID" if order["paid"] else "UNPAID"
                    action = (
                        f'<a class="button secondary small" href="/orders/confirm?order={order["id"]}">Confirm</a>'
                        if not order["paid"] else ""
                    )
                    order_rows.append(
                        f'<tr><td>#{order["id"]}</td><td>{esc(product.get("name", "Unknown"))}</td>'
                        f'<td>{int(order.get("quantity", 1))}</td><td>{_money(order["total"])}</td>'
                        f'<td><span class="demo-label">{status}</span></td><td>{action}</td></tr>'
                    )
                rows = "".join(order_rows)
                body = f"""
<div class="section-head"><div><span class="eyebrow">Account</span><h2>Order history</h2>
<p class="muted">Showing orders associated with the current demo cookie.</p></div></div>
{('<div class="table-wrap"><table><thead><tr><th>Order</th><th>Product</th><th>Qty</th><th>Total</th><th>Status</th><th>Action</th></tr></thead><tbody>'+rows+'</tbody></table></div>' if rows else '<div class="panel empty"><h3>No orders yet</h3><a class="button" href="/products">Start shopping</a></div>')}
<div class="warning">V4 demonstration: the order confirmation action does not verify payment.</div>"""
            success = query.get("success", [""])[0]
            notice = f"Demo order #{success} created; no payment was processed." if success else ""
            return self._send(200, page("Orders", body, user, notice))
        if path == "/orders/confirm":
            try:
                order_id = int(query.get("order", ["0"])[0])
                order = DB["orders"][order_id]
            except (ValueError, KeyError):
                return self._send(404, page("Order not found", '<div class="panel empty"><h2>Order not found</h2></div>', user))
            order["paid"] = True
            return self._redirect("/orders?" + urlencode({"notice": f"Order #{order_id} confirmed without payment"}))
        if path == "/profile":
            account = DB["users"].get(user) if user else None
            if not account:
                body = f'<div class="panel empty"><h2>Sign in to view this account</h2><a class="button" href="/login">Sign in</a></div>'
            else:
                body = f"""
<div class="section-head"><div><span class="eyebrow">Your account</span><h2>Profile</h2>
<p class="muted">Local demo identity and simulated account credit.</p></div></div>
<div class="layout"><section class="panel stack"><div class="spread"><span>Username</span><b>{esc(user)}</b></div>
<div class="spread"><span>Role</span><b>{esc(account['role'])}</b></div>
<div class="spread"><span>Store credit</span><b>{_money(account['credit'])}</b></div></section>
<aside class="panel"><h3>Lab identity</h3><p class="muted">The browser cookie is the only identity token in this intentionally vulnerable app.</p>
<a class="button ghost" href="/orders">View order history</a></aside></div>"""
            return self._send(200, page("Profile", body, user))
        if path == "/admin":
            # V7: this sensitive table is intentionally available without authentication.
            rows = "".join(
                f"<tr><td>{esc(name)}</td><td>{esc(account['role'])}</td><td>{_money(account['credit'])}</td></tr>"
                for name, account in DB["users"].items()
            )
            body = f"""
<div class="section-head"><div><span class="eyebrow">Restricted area - intentionally open</span>
<h2>Admin overview</h2><p class="muted">This page is unauthenticated by design (V7).</p></div>
<span class="demo-label">NO ROLE CHECK</span></div>
<div class="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Simulated credit</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="warning">Do not use real identities or data in this local education lab.</div>"""
            return self._send(200, page("Admin", body, user))
        match = re.fullmatch(r"/api/orders/(\d+)", path)
        if match:
            order = DB["orders"].get(int(match.group(1)))
            if not order:
                return self._json(404, {"error": "no such order"})
            return self._json(200, order)
        if path == "/api/confirm":
            try:
                order = DB["orders"][int(query.get("order", ["0"])[0])]
            except (ValueError, KeyError):
                return self._json(404, {"error": "no such order"})
            order["paid"] = True
            return self._json(200, {"confirmed": True, "order": order})
        return self._send(404, page("Not found", '<div class="panel empty"><h2>Page not found</h2><a class="button" href="/">Back home</a></div>', user))

    def do_POST(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        user = self._current_user()

        if path == "/api/login":
            body = self._body()
            username = body.get("username", "")
            account = DB["users"].get(username)
            if account and account["password"] == body.get("password"):
                return self._send(200, json.dumps({"ok": True}), "application/json",
                                  cookie=f"user={username}; Path=/")
            return self._json(401, {"error": "bad credentials"})
        if path == "/login":
            form = self._form()
            username = form.get("username", "")
            account = DB["users"].get(username)
            if account and account["password"] == form.get("password"):
                return self._redirect("/", f"user={username}; Path=/")
            return self._send(401, page("Sign in", _login_form("Incorrect username or password."), user))
        if path == "/cart/add":
            form = self._form()
            try:
                product_id = int(form.get("product_id", "0"))
                quantity = int(form.get("quantity", "1"))
                if product_id not in DB["products"]:
                    raise ValueError
            except ValueError:
                return self._send(400, page("Invalid item", '<div class="panel empty"><h2>Item could not be added.</h2></div>', user))
            key, cart = self._user_cart()
            cart[product_id] = cart.get(product_id, 0) + quantity
            return self._redirect("/cart?" + urlencode({"notice": "Item added to your cart"}))
        if path == "/cart/update":
            form = self._form()
            try:
                product_id = int(form.get("product_id", "0"))
                quantity = int(form.get("quantity", "1"))
                key, cart = self._user_cart()
                if product_id in cart:
                    cart[product_id] = quantity
            except ValueError:
                return self._send(400, page("Invalid quantity", '<div class="panel empty"><h2>Quantity could not be updated.</h2></div>', user))
            return self._redirect("/cart")
        if path == "/cart/remove":
            form = self._form()
            try:
                product_id = int(form.get("product_id", "0"))
                key, cart = self._user_cart()
                cart.pop(product_id, None)
            except ValueError:
                return self._send(400, page("Invalid item", '<div class="panel empty"><h2>Item could not be removed.</h2></div>', user))
            return self._redirect("/cart")
        if path == "/cart/coupon":
            form = self._form()
            code = str(form.get("code", "")).upper()
            try:
                subtotal = float(form.get("subtotal", "0"))
            except ValueError:
                return self._send(400, page("Invalid coupon amount", '<div class="panel empty"><h2>Subtotal is invalid.</h2></div>', user))
            percentage = DB["coupons"].get(code)
            if percentage is None:
                return self._send(400, page("Invalid coupon", '<div class="panel empty"><h2>That coupon code is not valid.</h2><a class="button" href="/cart">Back to cart</a></div>', user))
            key = user or "guest"
            DB["coupon_results"][key] = {
                "code": code,
                "discount_percent": percentage,
                "new_subtotal": round(subtotal * (1 - percentage / 100), 2),
            }
            return self._redirect("/cart")
        if path == "/checkout":
            form = self._form()
            try:
                product_id = int(form.get("product_id", "0"))
                quantity = int(form.get("quantity", "1"))
                client_price = float(form.get("price", "0"))
            except ValueError:
                return self._send(400, page("Invalid checkout", '<div class="panel empty"><h2>Checkout details are invalid.</h2></div>', user))
            if product_id not in DB["products"]:
                return self._send(400, page("Invalid product", '<div class="panel empty"><h2>Product is not available.</h2></div>', user))
            if not user:
                return self._redirect("/login")
            cart = DB["carts"].get(user, {})
            items = [
                {"product_id": int(item_id), "quantity": int(count)}
                for item_id, count in cart.items()
                if int(item_id) in DB["products"]
            ]
            order_id = self._create_order(user, product_id, client_price, quantity, items)
            DB["carts"].pop(user, None)
            return self._redirect(f"/orders?success={order_id}")

        if path == "/api/checkout":
            body = self._body()
            username = user
            if not username:
                return self._json(401, {"error": "login first"})
            try:
                product_id = int(body.get("product_id", 0))
                client_price = float(body.get("price", 0))
            except (TypeError, ValueError):
                return self._json(400, {"error": "invalid checkout data"})
            if product_id not in DB["products"]:
                return self._json(400, {"error": "unknown product"})
            # V1: price comes from the client and is deliberately trusted.
            order_id = self._create_order(username, product_id, client_price)
            return self._json(200, {"order_id": order_id, "charged": client_price})
        if path == "/api/apply_coupon":
            body = self._body()
            code = str(body.get("code", "")).upper()
            try:
                subtotal = float(body.get("subtotal", 0))
            except (TypeError, ValueError):
                return self._json(400, {"error": "invalid subtotal"})
            percentage = DB["coupons"].get(code)
            if percentage is None:
                return self._json(400, {"error": "invalid coupon"})
            # V2: no per-user or per-order coupon-use tracking.
            return self._json(200, {
                "discount_percent": percentage,
                "new_subtotal": round(subtotal * (1 - percentage / 100), 2),
            })
        return self._send(404, page("Not found", '<div class="panel empty"><h2>Page not found</h2><a class="button" href="/">Back home</a></div>', user))


if __name__ == "__main__":
    print(f"Naive Shop (INTENTIONALLY VULNERABLE) listening on http://{HOST}:{PORT}/")
    print("Localhost only. Disposable in-memory data. Press Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
