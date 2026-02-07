#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if ! "$PYTHON_BIN" -c "import alembic" >/dev/null 2>&1; then
  echo "migration_check: bootstrap skip (alembic not installed)"
  exit 0
fi

TMP_DB="backend/.migration_check.sqlite"
export OCG_DATABASE_URL="sqlite+pysqlite:///$(pwd)/$TMP_DB"

PYTHONPATH=backend "$PYTHON_BIN" -m ocg.cli migrate up
PYTHONPATH=backend "$PYTHON_BIN" -m ocg.cli migrate down

rm -f "$TMP_DB"
echo "migration_check: pass"
