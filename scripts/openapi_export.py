from __future__ import annotations

import json
from pathlib import Path

from ocg.main import create_app


def main() -> None:
    app = create_app()
    target = Path("docs/openapi/openapi.v1.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()

