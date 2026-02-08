#!/usr/bin/env sh
set -eu

sh scripts/docs_guard.sh

PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ]; then
  if "$PYTHON_BIN" -c "import ruff" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m ruff check backend
  elif [ "$STRICT_CHECKS" = "1" ]; then
    echo "lint: ruff is required in strict mode"
    exit 1
  else
    echo "lint: bootstrap skip (ruff not installed)"
  fi
else
  echo "lint: bootstrap skip (backend/pyproject.toml missing)"
fi

"$PYTHON_BIN" scripts/dependency_lint.py
