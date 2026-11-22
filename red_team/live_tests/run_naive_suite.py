"""Start the loopback-only Naive Shop when needed, run V1-V7, and stop only our child."""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "naive_shop" / "app.py"
ATTACK = ROOT / "red_team" / "live_tests" / "attack_naive.py"
URL = "http://127.0.0.1:8010/"


def existing_naive_shop():
    try:
        with urllib.request.urlopen(URL, timeout=1) as response:
            body = response.read(64_000).decode("utf-8", "replace")
            return response.status == 200 and "Naive Shop Lab" in body
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def stop_owned_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        command = (
            f"Stop-Process -Id {int(process.pid)} -ErrorAction Stop"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Naive Shop child PID {process.pid} did not stop cleanly.")


def main():
    owned_process = None
    if existing_naive_shop():
        print("Using existing Naive Shop at 127.0.0.1:8010; it will not be stopped.")
    else:
        owned_process = subprocess.Popen(
            [sys.executable, str(APP)],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if owned_process.poll() is not None:
                raise RuntimeError(
                    f"Naive Shop child exited before readiness (PID {owned_process.pid})."
                )
            if existing_naive_shop():
                break
            time.sleep(0.25)
        else:
            stop_owned_process(owned_process)
            owned_process = None
            raise RuntimeError("Naive Shop did not become ready on 127.0.0.1:8010.")
        print(f"Started Naive Shop child PID {owned_process.pid} on 127.0.0.1:8010.")

    try:
        result = subprocess.run(
            [sys.executable, str(ATTACK), "--test", "all"],
            cwd=str(ROOT),
            check=False,
        )
        print(f"V1-V7 runner exit code: {result.returncode}")
        return result.returncode
    finally:
        if owned_process is not None:
            stop_owned_process(owned_process)
            print(f"Stopped Naive Shop child PID {owned_process.pid}.")


if __name__ == "__main__":
    raise SystemExit(main())
