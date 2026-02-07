#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ] && "$PYTHON_BIN" -c "import mypy" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m mypy backend/ocg
else
  echo "typecheck: bootstrap skip (mypy not installed)"
fi
