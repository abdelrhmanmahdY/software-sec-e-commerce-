"""
Lab 3 demo - 2FA broken logic: client-controlled identity + unbounded brute force.

Fully in-memory simulation. No network, no real site, standard library only.

  * NaiveServer : trusts a client 'verify' value for identity, and never
                  limits 2FA attempts (VULNERABLE)
  * SecureServer: identity comes from the server-side session, and attempts
                  are locked out after a few tries (SAFE)

Run: python auth_identity_demo.py
"""
import secrets


class NaiveServer:
    """Models the PortSwigger lab flaw, locally and safely."""
    def __init__(self):
        # The real code each user would receive by email.
        self.codes = {"wiener": "0000", "carlos": f"{secrets.randbelow(10000):04d}"}
        self.attempts = 0

    def login2(self, verify_value, mfa_code):
        # BUG 1: identity is whatever the client put in 'verify'.
        target = verify_value
        # BUG 2: no attempt limit.
        self.attempts += 1
        return self.codes.get(target) == mfa_code


class SecureServer:
    def __init__(self):
        self.codes = {"wiener": "0000", "carlos": f"{secrets.randbelow(10000):04d}"}
        self.max_attempts = 5
        self.attempts = 0

    def login2(self, session_user, mfa_code):
        # FIX 1: identity comes from the trusted server-side session only.
        # FIX 2: lock out after a few attempts.
        if self.attempts >= self.max_attempts:
            raise PermissionError("locked out - too many attempts")
        self.attempts += 1
        return self.codes.get(session_user) == mfa_code


def brute_force(server, use_secure, session_user="wiener"):
    """Try to log in as carlos. Returns (found_code, attempts)."""
    for n in range(10000):
        code = f"{n:04d}"
        try:
            if use_secure:
                ok = server.login2(session_user, code)   # forced to session identity
            else:
                ok = server.login2("carlos", code)        # attacker forges identity
        except PermissionError:
            return None, server.attempts
        if ok:
            return code, server.attempts
    return None, server.attempts


def main():
    print("Lab 3 demo - broken 2FA logic\n")

    naive = NaiveServer()
    code, tries = brute_force(naive, use_secure=False)
    print(f"[NAIVE ] forged verify=carlos, brute-forced code={code} in {tries} tries   (VULNERABLE)")

    secure = SecureServer()
    code, tries = brute_force(secure, use_secure=True, session_user="wiener")
    print(f"[SECURE] identity forced to session 'wiener'; after {tries} tries -> carlos not reached   (SAFE)")


if __name__ == "__main__":
    main()
