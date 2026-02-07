from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_py_files(path: Path) -> list[Path]:
    return sorted([p for p in path.rglob("*.py") if "__pycache__" not in p.parts])


def main() -> int:
    errors: list[str] = []
    workers_files = collect_py_files(ROOT / "backend" / "ocg" / "workers")
    for file in workers_files:
        text = read_text(file)
        if "ocg.api" in text:
            errors.append(f"{file}: workers must not import API layer")

    frontend_files = sorted((ROOT / "frontend").rglob("*.*"))
    for file in frontend_files:
        if file.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = read_text(file)
        if "from \"ocg." in text or "from 'ocg." in text:
            errors.append(f"{file}: frontend must not import backend modules")

    permission_refs = 0
    service_files = collect_py_files(ROOT / "backend" / "ocg")
    for file in service_files:
        text = read_text(file)
        if "PermissionEvaluator" in text:
            permission_refs += 1
    if permission_refs < 2:
        errors.append("PermissionEvaluator not reused across modules as required.")

    if errors:
        for err in errors:
            print(f"dependency_lint: {err}")
        return 1
    print("dependency_lint: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

