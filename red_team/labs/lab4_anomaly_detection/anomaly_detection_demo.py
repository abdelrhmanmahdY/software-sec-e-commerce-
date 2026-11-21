"""
Lab 4.2 demo - behavioral anomaly detection with the z-score.

This is the Lab 4.2 exercise completed (the four functions filled in).
Standard library only (statistics). Offline. Run: python anomaly_detection_demo.py

It validates the DEFENSE: a real user is allowed; a pasting bot and a slow
attacker are both flagged.
"""
import statistics

# A user's NORMAL profile: seconds to type the password across trusted logins.
typing_history = [1.20, 1.35, 1.28, 1.22, 1.31, 1.26, 1.24, 1.30]

attempts = [
    ("Legit user, slightly tired", 1.40),
    ("Bot pasting the password",   0.15),
    ("Attacker typing, unsure",    2.90),
]

THRESHOLD = 3.0


def mean_time(samples):
    return statistics.mean(samples)


def std_time(samples):
    return statistics.pstdev(samples)


def z_score(value, mean, std):
    if std == 0:
        std = 0.1
    return abs(value - mean) / std


def is_anomaly(value, mean, std, threshold):
    return z_score(value, mean, std) > threshold


def main():
    m = mean_time(typing_history)
    s = std_time(typing_history)
    print(f"Normal typing: mean={m:.2f}s  std={s:.2f}s\n")
    for name, t in attempts:
        z = z_score(t, m, s)
        hit = is_anomaly(t, m, s, THRESHOLD)
        tag = "ANOMALY -> block / MFA" if hit else "OK -> allow"
        print(f"{name:28s} t={t:.2f}s  z={z:5.2f}  {tag}")


if __name__ == "__main__":
    main()
