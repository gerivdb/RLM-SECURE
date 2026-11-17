# Sovereign CI Pipeline for RLM Services
# Uses KIX as orchestrator, pytest for tests, KIVA-CLI for cross-repo sync

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import urllib.error


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    """Wait for service to respond on port."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            url = f"http://localhost:{port}/healthz"
            urllib.request.urlopen(url, timeout=1.0)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def main() -> int:
    print("[CI] Starting sovereign pipeline...")

    # 1. Start KIX orchestrator
    print("[CI] Starting KIX on port 8800...")
    kix_proc = subprocess.Popen(
        [sys.executable, "src/app.py"],
        cwd="D:/DO/WEB/TOOLS/L2-PLATFORM/KIX",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_port(8800):
        print("[CI] ERROR: KIX failed to start")
        return 1

    print("[CI] KIX is healthy")

    # 2. Start RLM-SECURE runner
    print("[CI] Starting RLM-SECURE on port 8797...")
    secure_proc = subprocess.Popen(
        [sys.executable, "src/app.py"],
        cwd="D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-SECURE",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_port(8797):
        print("[CI] ERROR: RLM-SECURE failed to start")
        return 1

    print("[CI] RLM-SECURE is healthy")

    # 3. Run tests
    print("[CI] Running tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd="D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-SECURE",
    )

    # Cleanup
    kix_proc.terminate()
    secure_proc.terminate()

    if result.returncode == 0:
        print("[CI] Pipeline completed successfully")
        return 0
    else:
        print("[CI] Pipeline failed")
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())