#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ]; then
  if "$PYTHON_BIN" -c "import ruff" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m ruff format --check backend
    exit 0
  fi
  if [ "$STRICT_CHECKS" = "1" ]; then
    echo "format_check: ruff is required in strict mode"
    exit 1
  fi
fi

echo "format_check: bootstrap skip (ruff not installed)"
