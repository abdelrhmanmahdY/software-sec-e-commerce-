"""
Lab 1 demo - Excessive trust in client-side controls.

Shows the difference between:
  * naive_checkout : trusts the price sent by the client (VULNERABLE)
  * secure_checkout: ignores the client price, uses the catalog price (SAFE)

Standard library only. Runs fully offline. Nothing is sent anywhere.
Run:  python naive_price_demo.py
"""

# The server's own source of truth. The client must never override this.
CATALOG = {
    "jacket": {"name": "Leather jacket", "price_cents": 133700},
    "lamp":   {"name": "Desk lamp",      "price_cents": 3499},
}

STORE_CREDIT_CENTS = 10000  # $100.00


def naive_checkout(product_id, client_price_cents):
    """VULNERABLE: trusts the price that came from the client request."""
    price = client_price_cents            # <-- the bug: client controls the money
    affordable = price <= STORE_CREDIT_CENTS
    return price, affordable


def secure_checkout(product_id, client_price_cents):
    """SAFE: ignores the client price, looks it up from the catalog."""
    product = CATALOG.get(product_id)
    if product is None:
        raise ValueError("unknown product")
    price = product["price_cents"]        # <-- source of truth is the server
    affordable = price <= STORE_CREDIT_CENTS
    return price, affordable


def _money(cents):
    return f"${cents / 100:,.2f}"


def main():
    print("Lab 1 demo - client-side price trust\n")
    print(f"Store credit: {_money(STORE_CREDIT_CENTS)}")
    print(f"Real jacket price: {_money(CATALOG['jacket']['price_cents'])}\n")

    tampered = 1  # attacker sends 1 cent
    print(f"Attacker tampers the request: price_cents = {tampered}\n")

    price, ok = naive_checkout("jacket", tampered)
    print(f"[NAIVE ] charged {_money(price)}  -> order allowed: {ok}   (VULNERABLE)")

    price, ok = secure_checkout("jacket", tampered)
    print(f"[SECURE] charged {_money(price)}  -> order allowed: {ok}   (SAFE)")


if __name__ == "__main__":
    main()
