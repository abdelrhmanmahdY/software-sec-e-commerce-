"""
Lab 2.3 demo - Insufficient workflow validation (reaching confirmation
without paying).

  * naive_confirm : marks an order complete whenever confirmation is requested
                    (VULNERABLE)
  * secure_confirm: only completes an order whose state is already PAID (SAFE)

Standard library only. Offline. Run: python workflow_skip_demo.py
"""


class Order:
    def __init__(self):
        self.state = "CART"          # CART -> CHECKOUT -> PAID -> CONFIRMED

    def pay(self, credit, total):
        if credit >= total:
            self.state = "PAID"


def naive_confirm(order):
    """VULNERABLE: trusts that confirmation is only reached after payment."""
    order.state = "CONFIRMED"        # no check of the real state
    return order.state


def secure_confirm(order):
    """SAFE: confirmation requires the order to be PAID first."""
    if order.state != "PAID":
        raise PermissionError(f"cannot confirm from state {order.state!r}")
    order.state = "CONFIRMED"
    return order.state


def main():
    print("Lab 2.3 demo - skip payment, replay confirmation\n")

    # Attacker never pays (jacket far above credit), jumps to confirmation.
    a = Order()
    print(f"Order state before confirm: {a.state!r}")
    print(f"[NAIVE ] confirm -> {naive_confirm(a)!r}   (VULNERABLE - never paid)\n")

    b = Order()
    print(f"Order state before confirm: {b.state!r}")
    try:
        secure_confirm(b)
    except PermissionError as exc:
        print(f"[SECURE] blocked: {exc}   (SAFE)")

    # And the legitimate path still works:
    b.pay(credit=100, total=50)
    print(f"[SECURE] after paying -> {secure_confirm(b)!r}   (legit path OK)")


if __name__ == "__main__":
    main()
