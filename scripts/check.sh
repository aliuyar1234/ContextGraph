#!/usr/bin/env sh
set -eu

PROFILE="${CHECK_PROFILE:-fast}"

case "$PROFILE" in
  fast|ci|full) ;;
  *)
    echo "Unsupported CHECK_PROFILE: $PROFILE"
    echo "Allowed values: fast, ci, full"
    exit 2
    ;;
esac

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

FAILED=0

print_stage() {
  echo
  echo "==> $1"
}

fail_stage() {
  echo "FAIL: $1"
  FAILED=1
}

pass_stage() {
  echo "PASS: $1"
}

run_script_if_present() {
  stage_name="$1"
  script_path="$2"
  if [ -f "$script_path" ]; then
    if sh "$script_path"; then
      pass_stage "$stage_name"
    else
      fail_stage "$stage_name"
    fi
  else
    pass_stage "$stage_name (bootstrap no-op)"
  fi
}

check_format() {
  if [ -f "scripts/format_check.sh" ]; then
    run_script_if_present "format" "scripts/format_check.sh"
    return
  fi
  pass_stage "format (bootstrap no-op)"
}

check_lint() {
  if [ -f "scripts/lint.sh" ]; then
    run_script_if_present "lint" "scripts/lint.sh"
    return
  fi
  pass_stage "lint (bootstrap no-op)"
}

check_typecheck() {
  if [ -f "scripts/typecheck.sh" ]; then
    run_script_if_present "typecheck" "scripts/typecheck.sh"
    return
  fi
  pass_stage "typecheck (bootstrap no-op)"
}

check_unit() {
  if [ -f "scripts/test_unit.sh" ]; then
    run_script_if_present "unit tests" "scripts/test_unit.sh"
    return
  fi
  pass_stage "unit tests (bootstrap no-op)"
}

check_integration() {
  if [ -f "scripts/test_integration.sh" ]; then
    run_script_if_present "integration tests" "scripts/test_integration.sh"
    return
  fi
  pass_stage "integration tests (bootstrap no-op)"
}

check_migrations() {
  if [ -f "scripts/migration_check.sh" ]; then
    run_script_if_present "migration check" "scripts/migration_check.sh"
    return
  fi
  if [ -d "migrations" ]; then
    pass_stage "migration check (migrations directory present)"
  else
    fail_stage "migration check (migrations directory missing)"
  fi
}

check_secrets() {
  if [ -f "scripts/secret_scan.sh" ]; then
    run_script_if_present "secret scan" "scripts/secret_scan.sh"
    return
  fi

  scan_paths=".github backend frontend ops scripts docs"
  has_match=0
  if command -v rg >/dev/null 2>&1; then
    if rg -n -I -l --hidden \
      --glob '!.git/*' \
      --glob '!MANIFEST.sha256' \
      --glob '!frontend/node_modules/*' \
      --glob '!.next/*' \
      --glob '!dist/*' \
      --glob '!build/*' \
      '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH|DSA|PGP)? ?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})' \
      $scan_paths; then
      has_match=1
    fi
  else
    if grep -RInE \
      --exclude-dir=.git \
      --exclude-dir=node_modules \
      --exclude-dir=.next \
      --exclude-dir=dist \
      --exclude-dir=build \
      '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH|DSA|PGP)? ?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})' \
      $scan_paths; then
      has_match=1
    fi
  fi

  if [ "$has_match" -eq 1 ]; then
    fail_stage "secret scan"
  else
    pass_stage "secret scan"
  fi
}

check_redaction() {
  if [ -f "scripts/redaction_scan.sh" ]; then
    run_script_if_present "redaction scan" "scripts/redaction_scan.sh"
    return
  fi

  log_roots=""
  [ -d "artifacts/logs" ] && log_roots="$log_roots artifacts/logs"
  [ -d "logs" ] && log_roots="$log_roots logs"

  if [ -z "$log_roots" ]; then
    pass_stage "redaction scan (no log artifacts yet)"
    return
  fi

  has_match=0
  for root in $log_roots; do
    if command -v rg >/dev/null 2>&1; then
      if rg -n '(Authorization:|Bearer [A-Za-z0-9._-]{12,}|api[_-]?key|token=|password=)' "$root"; then
        has_match=1
      fi
    else
      if grep -RInE '(Authorization:|Bearer [A-Za-z0-9._-]{12,}|api[_-]?key|token=|password=)' "$root"; then
        has_match=1
      fi
    fi
  done

  if [ "$has_match" -eq 1 ]; then
    fail_stage "redaction scan"
  else
    pass_stage "redaction scan"
  fi
}

check_perf_smoke() {
  if [ -f "scripts/perf_smoke.sh" ]; then
    run_script_if_present "perf smoke" "scripts/perf_smoke.sh"
    return
  fi
  pass_stage "perf smoke (bootstrap no-op)"
}

check_api_compat() {
  if [ -f "scripts/openapi_check.sh" ]; then
    run_script_if_present "api compatibility" "scripts/openapi_check.sh"
    return
  fi
  pass_stage "api compatibility (bootstrap no-op)"
}

print_stage "check profile: $PROFILE"

print_stage "format"
check_format

print_stage "lint"
check_lint

print_stage "typecheck"
check_typecheck

print_stage "unit tests"
check_unit

if [ "$PROFILE" = "ci" ] || [ "$PROFILE" = "full" ]; then
  print_stage "integration tests"
  check_integration
fi

print_stage "migration check"
check_migrations

print_stage "secret scan"
check_secrets

print_stage "redaction scan"
check_redaction

if [ "$PROFILE" = "full" ]; then
  print_stage "perf smoke"
  check_perf_smoke
fi

if [ "$PROFILE" = "ci" ] || [ "$PROFILE" = "full" ]; then
  print_stage "api compatibility"
  check_api_compat
fi

if [ "$FAILED" -ne 0 ]; then
  echo
  echo "check failed"
  exit 1
fi

echo
echo "check passed"
