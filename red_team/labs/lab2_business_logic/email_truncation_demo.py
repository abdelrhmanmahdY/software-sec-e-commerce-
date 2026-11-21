"""
Lab 2.2 demo - Inconsistent handling of exceptional input (email truncation).

  * naive_register : stores only the first 255 chars, then grants admin by the
                     stored email's domain (VULNERABLE)
  * secure_register: rejects over-long input and never grants roles by domain (SAFE)

Standard library only. Offline. Run: python email_truncation_demo.py
"""

MAX_EMAIL_LEN = 254  # RFC 5321 practical limit; enforced as a hard reject when secure
ADMIN_DOMAIN = "dontwannacry.com"


def domain_of(email):
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def naive_register(email):
    """VULNERABLE: silently truncates to 255, then trusts the truncated domain."""
    stored = email[:255]                      # silent truncation
    is_admin = domain_of(stored) == ADMIN_DOMAIN
    return stored, is_admin


def secure_register(email):
    """SAFE: reject over-long input; role is NOT derived from the email domain."""
    if len(email) > MAX_EMAIL_LEN:
        raise ValueError("email too long - rejected")
    stored = email
    is_admin = False                          # roles are assigned explicitly, elsewhere
    return stored, is_admin


def main():
    print("Lab 2.2 demo - email truncation -> admin\n")
    # Craft an address whose char 255 is the final 'm' of '@dontwannacry.com'.
    prefix_len = 255 - len("@dontwannacry.com")
    crafted = "a" * prefix_len + "@dontwannacry.com" + ".attacker-inbox.net"
    print(f"Crafted email length: {len(crafted)} chars")
    print(f"...ends with: ...{crafted[-40:]}\n")

    stored, admin = naive_register(crafted)
    print(f"[NAIVE ] stored domain = {domain_of(stored)!r:22} admin granted: {admin}   (VULNERABLE)")

    try:
        stored, admin = secure_register(crafted)
        print(f"[SECURE] stored, admin granted: {admin}")
    except ValueError as exc:
        print(f"[SECURE] rejected: {exc}   (SAFE)")


if __name__ == "__main__":
    main()
