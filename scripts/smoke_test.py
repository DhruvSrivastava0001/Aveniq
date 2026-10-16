"""Non-destructive ChurnIQ integration smoke test for a running local stack.

Run after MySQL, Spring Boot, and FastAPI are started and customer rows exist:
    python scripts/smoke_test.py
Optional URLs:
    python scripts/smoke_test.py --python-url http://127.0.0.1:8003 --spring-url http://localhost:8080
"""
from __future__ import annotations

import argparse
import sys
import requests


def check(name: str, url: str, *, method: str = "GET", json_body=None) -> tuple[bool, str]:
    try:
        response = requests.request(method, url, json=json_body, timeout=10)
        if not response.ok:
            try:
                detail = response.json().get("detail", response.text[:250])
            except ValueError:
                detail = response.text[:250]
            return False, f"HTTP {response.status_code}: {detail}"
        return True, f"HTTP {response.status_code}"
    except requests.RequestException as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-url", default="http://127.0.0.1:8003")
    parser.add_argument("--spring-url", default="http://localhost:8080")
    args = parser.parse_args()
    py = args.python_url.rstrip("/")
    spring = args.spring_url.rstrip("/")
    results: list[tuple[str, bool, str]] = []

    for name, url, method, body in [
        ("FastAPI liveness", f"{py}/health", "GET", None),
        ("Spring Boot customer page / MySQL", f"{spring}/api/customers/page?page=0&size=1", "GET", None),
        ("Live customer intelligence overview", f"{py}/api/intelligence/overview", "GET", None),
        ("Grounded customer question", f"{py}/api/intelligence/chat", "POST", {"question": "How many customers are recorded in the current dataset?"}),
        ("Alert settings", f"{py}/api/intelligence/alerts", "GET", None),
    ]:
        ok, detail = check(name, url, method=method, json_body=body)
        results.append((name, ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if name == "FastAPI liveness" and ok:
            try:
                health = requests.get(url, timeout=10).json()
                version = health.get("scikit_learn_version")
                expected = health.get("expected_scikit_learn_version", "1.7.2")
                compatible = health.get("model_compatibility") == "compatible_version"
                results.append(("scikit-learn model compatibility", compatible, f"installed={version}; expected={expected}"))
                print(f"{'PASS' if compatible else 'FAIL'}  scikit-learn model compatibility: installed={version}; expected={expected}")
            except (requests.RequestException, ValueError):
                pass

    failures = [item for item in results if not item[1]]
    print(f"\nResult: {len(results) - len(failures)}/{len(results)} checks passed.")
    if failures:
        print("This smoke test is non-destructive and does not replace browser-level CRUD/import/prediction tests.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
