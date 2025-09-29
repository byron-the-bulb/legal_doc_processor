#!/usr/bin/env bash
# Set Fly.io app secrets from a .env file
#
# Usage:
#   backend/scripts/set-fly-secrets.sh [--app APP_NAME] [--env-file PATH] [--all]
#
# Defaults:
#   --app       -> taken from fly.toml (app = '...') if present, otherwise required
#   --env-file  -> prefers backend/.env, falls back to repo .env
#   without --all, only an allowlist of keys is pushed (recommended)
#
# Notes:
# - Lines starting with # are ignored. Supports optional `export KEY=VALUE` syntax.
# - Values may be quoted with single or double quotes.
# - Requires `fly` CLI installed and authenticated.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

APP=""
ENV_FILE=""
PUSH_ALL=false

# Default allowlist (adjust as needed). Kept simple for macOS Bash 3.2 compatibility.
# Explicitly control which keys become secrets.
ALLOWLIST=(
  OPENAI_API_KEY
  OPENAI_MODEL
  DATABASE_URL
  REDIS_URL
  BROKER_URL
  CELERY_RESULT_BACKEND
  ENV
  POPPLER_PATH
  PIPELINE_LOG_LEVEL
  PARSER_LOG_LEVEL
  DOC_CLS_LOG_LEVEL
  LOG_LEVEL
  S3_ENDPOINT
  S3_ACCESS_KEY
  S3_SECRET_KEY
  S3_BUCKET
)

usage() {
  cat <<USAGE
Set Fly.io secrets from a .env file

Options:
  --app APP_NAME        Fly app name (defaults to value in backend/fly.toml if present)
  --env-file PATH       Path to .env file (defaults to backend/.env then ./.env)
  --all                 Push all keys found in the .env (ignore allowlist)
  -h, --help            Show this help

Examples:
  ${0} --app my-app --env-file backend/.env
  ${0} --all            # push every KEY=VALUE from the chosen .env
USAGE
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --app)
        APP="${2:-}"
        shift 2
        ;;
      --env-file)
        ENV_FILE="${2:-}"
        shift 2
        ;;
      --all)
        PUSH_ALL=true
        shift 1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        usage
        exit 1
        ;;
    esac
  done
}

ensure_fly() {
  if ! command -v fly >/dev/null 2>&1; then
    echo "Error: fly CLI not found. Install with: brew install flyctl" >&2
    exit 1
  fi
}

infer_app_from_fly_toml() {
  local toml="${BACKEND_DIR}/fly.toml"
  if [[ -n "$APP" ]]; then return; fi
  if [[ -f "$toml" ]]; then
    local val
    val=$(grep -E "^app\s*=\s*'[^']+'" "$toml" | head -n1 | sed -E "s/.*'([^']+)'.*/\1/") || true
    if [[ -n "$val" ]]; then
      APP="$val"
    fi
  fi
}

choose_env_file() {
  if [[ -n "$ENV_FILE" ]]; then return; fi
  if [[ -f "${BACKEND_DIR}/.env" ]]; then
    ENV_FILE="${BACKEND_DIR}/.env"
  elif [[ -f "${REPO_ROOT}/.env" ]]; then
    ENV_FILE="${REPO_ROOT}/.env"
  else
    echo "Error: No .env file found. Provide --env-file PATH" >&2
    exit 1
  fi
}

in_allowlist() {
  local key="$1"
  for k in "${ALLOWLIST[@]}"; do
    if [[ "$k" == "$key" ]]; then
      return 0
    fi
  done
  return 1
}

collect_pairs() {
  local line key val
  PAIRS=()

  while IFS= read -r line || [[ -n "$line" ]]; do
    # Trim leading/trailing whitespace (portable for macOS Bash 3.2)
    line="$(printf '%s' "$line" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
    # Skip comments/blank lines
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    # Drop leading 'export '
    if [[ "$line" =~ ^export[[:space:]]+ ]]; then
      line="${line#export }"
    fi
    # Match KEY=VALUE
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      # Strip surrounding quotes if present
      if [[ "$val" =~ ^"(.*)"$ ]]; then val="${BASH_REMATCH[1]}"; fi
      if [[ "$val" =~ ^'(.*)'$ ]]; then val="${BASH_REMATCH[1]}"; fi
      # Skip if not in allowlist (unless --all)
      if ! $PUSH_ALL && ! in_allowlist "$key"; then
        continue
      fi
      # Append as a single array item to preserve spaces
      PAIRS+=("${key}=${val}")
    fi
  done < "$ENV_FILE"
}

main() {
  parse_args "$@"
  ensure_fly()
  infer_app_from_fly_toml()
  choose_env_file()

  if [[ -z "$APP" ]]; then
    echo "Error: --app not provided and app not found in backend/fly.toml" >&2
    exit 1
  fi

  echo "Using app: $APP"
  echo "Using env file: $ENV_FILE"
  $PUSH_ALL || echo "Using allowlist (override with --all)"

  collect_pairs

  if [[ ${#PAIRS[@]} -eq 0 ]]; then
    echo "No secrets to set (check allowlist or use --all)." >&2
    exit 1
  fi

  echo "Setting ${#PAIRS[@]} secret(s) on Fly..."
  # shellcheck disable=SC2086
  fly secrets set "${PAIRS[@]}" -a "$APP"
  echo "Done."
}

main "$@"
