#!/usr/bin/env sh
set -eu

collect_changed_files() {
  if [ "$#" -gt 0 ]; then
    printf '%s\n' "$@"
    return
  fi

  if [ -n "${CHANGED_FILES:-}" ]; then
    printf '%s\n' "$CHANGED_FILES" | tr ' ' '\n' | sed '/^$/d'
    return
  fi

  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if [ -n "${DOCS_GUARD_BASE:-}" ]; then
      git diff --name-only --diff-filter=ACMRTUXB "${DOCS_GUARD_BASE}"...HEAD
      return
    fi

    if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
      git diff --name-only --diff-filter=ACMRTUXB HEAD~1...HEAD
      return
    fi

    git diff-tree --no-commit-id --name-only -r HEAD
    return
  fi

  printf ''
}

has_match() {
  pattern="$1"
  printf '%s\n' "$CHANGED" | grep -E "$pattern" >/dev/null 2>&1
}

ensure_spec_updated() {
  trigger_name="$1"
  trigger_pattern="$2"
  required_spec_pattern="$3"
  required_spec_file="$4"

  if has_match "$trigger_pattern"; then
    if ! has_match "$required_spec_pattern"; then
      echo "docs_guard: $trigger_name changed without updating $required_spec_file"
      VIOLATION=1
    fi
    CRITICAL_SURFACE_TOUCHED=1
  fi
}

CHANGED="$(collect_changed_files "$@")"

if [ -z "$CHANGED" ]; then
  echo "docs_guard: no changed files detected; skipping"
  exit 0
fi

VIOLATION=0
CRITICAL_SURFACE_TOUCHED=0

# API contracts and route surfaces.
ensure_spec_updated \
  "API routes/contracts" \
  '^(backend/.*/api/|backend/api/|backend/.*/routes/|frontend/.*/api/|openapi/)' \
  '^spec/04_INTERFACES_AND_CONTRACTS\.md$' \
  'spec/04_INTERFACES_AND_CONTRACTS.md'

# DB schema and migration surfaces.
ensure_spec_updated \
  "DB schema/migrations" \
  '^(migrations/|backend/.*/models/|backend/.*/schema/|backend/.*/alembic/)' \
  '^spec/05_DATASTORE_AND_MIGRATIONS\.md$' \
  'spec/05_DATASTORE_AND_MIGRATIONS.md'

# Security posture/auth surfaces.
ensure_spec_updated \
  "security controls" \
  '^(backend/.*/auth/|backend/.*/security/|ops/.*/auth|ops/.*/security|frontend/.*/auth/)' \
  '^spec/06_SECURITY_AND_THREAT_MODEL\.md$' \
  'spec/06_SECURITY_AND_THREAT_MODEL.md'

# Hot paths / critical performance flow surfaces.
ensure_spec_updated \
  "hot paths" \
  '^(backend/.*/analytics/|backend/.*/suggest/|backend/.*/ingest/|backend/.*/connector/|backend/.*/aggregate/)' \
  '^spec/02_ARCHITECTURE\.md$' \
  'spec/02_ARCHITECTURE.md'

if [ "$CRITICAL_SURFACE_TOUCHED" -eq 1 ]; then
  if ! has_match '^DECISIONS\.md$' && ! has_match '^ASSUMPTIONS\.md$'; then
    echo "docs_guard: critical-surface change requires DECISIONS.md or ASSUMPTIONS.md update"
    VIOLATION=1
  fi
fi

if [ "$VIOLATION" -ne 0 ]; then
  exit 1
fi

echo "docs_guard: pass"
