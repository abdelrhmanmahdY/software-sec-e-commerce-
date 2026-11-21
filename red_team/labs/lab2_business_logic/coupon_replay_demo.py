"""
Lab 2.1 demo - Flawed enforcement of business rules (coupon stacking).

  * naive_apply : rejects a coupon only if it equals the LAST one applied,
                  so alternating two codes stacks the discount (VULNERABLE)
  * secure_apply: remembers ALL used codes and caps the total discount (SAFE)

Standard library only. Offline. Run: python coupon_replay_demo.py
"""

COUPONS = {"NEWCUST5": 5, "SIGNUP30": 30}  # percent off
MAX_TOTAL_DISCOUNT = 30                      # business cap used by the secure version


def naive_apply(sequence):
    """VULNERABLE: only blocks an immediate repeat of the same code."""
    last = None
    total = 0
    for code in sequence:
        if code == last:
            continue                 # the only check: same as previous
        total += COUPONS.get(code, 0)
        last = code
    return min(total, 100)


def secure_apply(sequence):
    """SAFE: each code counts once, and the total is capped."""
    used = set()
    total = 0
    for code in sequence:
        if code in used:
            continue                 # already used -> reject
        if code not in COUPONS:
            continue
        used.add(code)
        total += COUPONS[code]
    return min(total, MAX_TOTAL_DISCOUNT)


def main():
    print("Lab 2.1 demo - coupon stacking\n")
    # attacker alternates the two codes 4 times
    attack = ["NEWCUST5", "SIGNUP30"] * 4
    print(f"Applied sequence ({len(attack)} codes): {attack}\n")
    print(f"[NAIVE ] total discount = {naive_apply(attack)}%   (VULNERABLE - stacks)")
    print(f"[SECURE] total discount = {secure_apply(attack)}%   (SAFE - capped, one use each)")


if __name__ == "__main__":
    main()
