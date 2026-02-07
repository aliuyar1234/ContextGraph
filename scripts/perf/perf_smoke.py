from __future__ import annotations

import json
import time
from pathlib import Path

import httpx


API_BASE = "http://127.0.0.1:8080"


def main() -> None:
    targets = [
        "/api/v1/analytics/processes/chat%3Aaction%3Dmessage/patterns",
        "/api/v1/suggest/next_steps",
    ]
    results = {}
    with httpx.Client(timeout=3.0, headers={"X-Dev-User": "demo-user", "X-Dev-Role": "analyst"}) as client:
        for path in targets:
            start = time.perf_counter()
            if path.endswith("next_steps"):
                resp = client.post(
                    f"{API_BASE}{path}",
                    json={"process_key": "chat:action=message", "recent_steps": [], "limit": 5},
                )
            else:
                resp = client.get(f"{API_BASE}{path}")
            elapsed_ms = (time.perf_counter() - start) * 1000
            results[path] = {"status": resp.status_code, "duration_ms": elapsed_ms}
    out = Path("artifacts/perf")
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("perf_smoke: wrote artifacts/perf/latest.json")


if __name__ == "__main__":
    main()

