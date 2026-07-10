import json
import os
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    path: str


BASE_URL = os.getenv(
    "SMOKE_BASE_URL",
    "http://127.0.0.1:8000/api/v1",
).rstrip("/")

TIMEOUT_SECONDS = float(os.getenv("SMOKE_TIMEOUT_SECONDS", "15"))

CHECKS = [
    SmokeCheck("Backend health", "/health"),
    SmokeCheck("Database health", "/health/database"),
    SmokeCheck("Chat module", "/chat/status"),
    SmokeCheck("Review module", "/review/status"),
    SmokeCheck("Planner module", "/planner/status"),
    SmokeCheck("Documentation module", "/documentation/status"),
    SmokeCheck("Evaluation module", "/evaluation/status"),
]


def run_check(check: SmokeCheck) -> bool:
    url = f"{BASE_URL}{check.path}"
    request = Request(url=url, method="GET")

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)

            if response.status != 200:
                print(f"[FAIL] {check.name}: HTTP {response.status}")
                return False

            print(f"[PASS] {check.name}: {payload}")
            return True

    except HTTPError as exc:
        print(f"[FAIL] {check.name}: HTTP {exc.code}")
        return False

    except URLError as exc:
        print(f"[FAIL] {check.name}: {exc.reason}")
        return False

    except (TimeoutError, json.JSONDecodeError, ValueError) as exc:
        print(f"[FAIL] {check.name}: {exc}")
        return False


def main() -> int:
    print(f"Running smoke tests against: {BASE_URL}")
    print()

    results = [run_check(check) for check in CHECKS]

    print()

    passed = sum(results)
    failed = len(results) - passed

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())