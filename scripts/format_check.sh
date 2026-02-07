#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ] && "$PYTHON_BIN" -c "import ruff" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m ruff format --check backend
  exit 0
fi

echo "format_check: bootstrap skip (ruff not installed)"
