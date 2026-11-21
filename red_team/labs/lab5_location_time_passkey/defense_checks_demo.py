"""
Lab 5 demo - location, time window, and passkey checks (defensive).

Reproduces the Lab 5 teaching printout. Standard library only (math).
Offline. Run: python defense_checks_demo.py

The three hands-on functions (haversine_km, time_allowed, passkey_allowed)
are implemented; the driver combines them as passkey -> location -> time.
"""
import math

HOME_LAT, HOME_LON = 30.0444, 31.2357
NEAR_LAT, NEAR_LON = 30.0131, 31.2089
LONDON_LAT, LONDON_LON = 51.5074, -0.1278
RADIUS_KM = 50.0
TIME_START, TIME_END = 8, 22


def haversine_km(lat1, lon1, lat2, lon2):
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = p2 - p1, l2 - l1
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def time_allowed(hour, start_hour, end_hour):
    return start_hour <= hour < end_hour


def passkey_allowed(credential_matches, signature_valid):
    return bool(credential_matches) and bool(signature_valid)


def decide(distance_km, hour, credential_matches, signature_valid):
    if not passkey_allowed(credential_matches, signature_valid):
        return "BLOCK (passkey)"
    if distance_km > RADIUS_KM:
        return "BLOCK (location)"
    if not time_allowed(hour, TIME_START, TIME_END):
        return "BLOCK (time)"
    return "ALLOW"


def main():
    print("Lab 5 demo - location, time, passkey\n")

    print("Location (radius 50 km)")
    for label, lat, lon in (
        ("Same point", HOME_LAT, HOME_LON),
        ("Nearby point", NEAR_LAT, NEAR_LON),
        ("London", LONDON_LAT, LONDON_LON),
    ):
        d = haversine_km(HOME_LAT, HOME_LON, lat, lon)
        place = "INSIDE" if d <= RADIUS_KM else "OUTSIDE"
        print(f"  {label:14s} {d:8.1f} km  {place}")

    print("\nTime window [8, 22)")
    for hour in (8, 21, 22, 3):
        print(f"  hour {hour:2d}  {'ALLOW' if time_allowed(hour, TIME_START, TIME_END) else 'BLOCK'}")

    print("\nPasskey (credential, signature)")
    for cred, sig in ((True, True), (True, False), (False, True)):
        print(f"  ({cred!s:5}, {sig!s:5}) -> {'ALLOW' if passkey_allowed(cred, sig) else 'BLOCK'}")

    print("\nCombined login (passkey -> location -> time)")
    near = haversine_km(HOME_LAT, HOME_LON, NEAR_LAT, NEAR_LON)
    far = haversine_km(HOME_LAT, HOME_LON, LONDON_LAT, LONDON_LON)
    for label, dist, hour, cred, sig in (
        ("Nearby, 10:00, good passkey", near, 10, True, True),
        ("London, 10:00, good passkey", far, 10, True, True),
        ("Nearby, 03:00, good passkey", near, 3, True, True),
        ("Nearby, 10:00, bad signature", near, 10, True, False),
    ):
        print(f"  {label:32s} {decide(dist, hour, cred, sig)}")


if __name__ == "__main__":
    main()
