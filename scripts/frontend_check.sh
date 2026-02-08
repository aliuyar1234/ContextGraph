#!/usr/bin/env sh
set -eu

STRICT_CHECKS="${STRICT_CHECKS:-0}"

if [ ! -f "frontend/package.json" ]; then
  echo "frontend_check: no frontend package found; skipping"
  exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
  if [ "$STRICT_CHECKS" = "1" ]; then
    echo "frontend_check: npm is required in strict mode"
    exit 1
  fi
  echo "frontend_check: bootstrap skip (npm not installed)"
  exit 0
fi

if [ ! -f "frontend/package-lock.json" ]; then
  if [ "$STRICT_CHECKS" = "1" ]; then
    echo "frontend_check: frontend/package-lock.json is required in strict mode"
    exit 1
  fi
  echo "frontend_check: bootstrap skip (package-lock.json missing)"
  exit 0
fi

npm --prefix frontend ci
npm --prefix frontend run build
echo "frontend_check: pass"
