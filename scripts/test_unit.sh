#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pytest backend/tests/unit -q
else
  echo "test_unit: bootstrap skip (pytest not installed)"
fi
