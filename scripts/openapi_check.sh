#!/usr/bin/env sh
set -eu

TMP="docs/openapi/.generated.json"
PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if ! "$PYTHON_BIN" -c "import fastapi" >/dev/null 2>&1; then
  if [ "$STRICT_CHECKS" = "1" ]; then
    echo "openapi_check: fastapi is required in strict mode"
    exit 1
  fi
  echo "openapi_check: bootstrap skip (fastapi not installed in active interpreter)"
  exit 0
fi

PYTHONPATH=backend "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
from ocg.main import create_app

doc = create_app().openapi()
path = Path("docs/openapi/.generated.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
PY

if [ ! -f "docs/openapi/openapi.v1.json" ]; then
  mv "$TMP" "docs/openapi/openapi.v1.json"
  echo "openapi_check: baseline created"
  exit 0
fi

if "$PYTHON_BIN" - <<'PY'
import json
import sys
from pathlib import Path

def normalize(doc):
    validation_props = (
        doc.get("components", {})
        .get("schemas", {})
        .get("ValidationError", {})
        .get("properties")
    )
    if isinstance(validation_props, dict):
        # FastAPI/Pydantic versions may add framework-level validation metadata
        # without changing our own API contract surface.
        validation_props.pop("input", None)
        validation_props.pop("ctx", None)
    return doc

generated = normalize(json.loads(Path("docs/openapi/.generated.json").read_text(encoding="utf-8")))
baseline = normalize(json.loads(Path("docs/openapi/openapi.v1.json").read_text(encoding="utf-8")))
sys.exit(0 if generated == baseline else 1)
PY
then
  rm -f "$TMP"
  echo "openapi_check: pass"
  exit 0
fi

echo "openapi_check: breaking or undocumented API change detected; update baseline intentionally"
exit 1
