#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
STRICT_CHECKS="${STRICT_CHECKS:-0}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pytest backend/tests/integration -q
elif [ "$STRICT_CHECKS" = "1" ]; then
  echo "test_integration: pytest is required in strict mode"
  exit 1
else
  echo "test_integration: bootstrap skip (pytest not installed)"
fi
