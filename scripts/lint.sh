#!/usr/bin/env sh
set -eu

sh scripts/docs_guard.sh

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ] && "$PYTHON_BIN" -c "import ruff" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m ruff check backend
else
  echo "lint: bootstrap skip (ruff not installed)"
fi

"$PYTHON_BIN" scripts/dependency_lint.py
