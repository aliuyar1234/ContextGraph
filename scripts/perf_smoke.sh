#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if "$PYTHON_BIN" -c "import httpx" >/dev/null 2>&1; then
  PYTHONPATH=backend "$PYTHON_BIN" scripts/perf/perf_smoke.py
elif [ "$STRICT_CHECKS" = "1" ]; then
  echo "perf_smoke: httpx is required in strict mode"
  exit 1
else
  echo "perf_smoke: bootstrap skip (httpx not installed)"
fi
