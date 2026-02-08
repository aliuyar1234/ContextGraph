#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ -f "backend/pyproject.toml" ]; then
  if "$PYTHON_BIN" -c "import mypy" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m mypy backend/ocg
  elif [ "$STRICT_CHECKS" = "1" ]; then
    echo "typecheck: mypy is required in strict mode"
    exit 1
  else
    echo "typecheck: bootstrap skip (mypy not installed)"
  fi
else
  echo "typecheck: bootstrap skip (backend/pyproject.toml missing)"
fi
