#!/usr/bin/env bash
# Minimal, function-free script to set Fly.io secrets from a .env file (macOS-friendly)
# Usage examples:
#   backend/scripts/set-fly-secrets-simple.sh --all
#   backend/scripts/set-fly-secrets-simple.sh --app <APP_NAME> --env-file backend/.env

set -euo pipefail

# Defaults
APP=""
ENV_FILE=""
PUSH_ALL=0

# Resolve paths relative to this script
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
BACKEND_DIR="${SCRIPT_DIR}/.."
REPO_ROOT="$(cd "${BACKEND_DIR}/.." && pwd)"

# Parse args (no functions)
while [ $# -gt 0 ]; do
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
      PUSH_ALL=1
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [--app APP_NAME] [--env-file PATH] [--all]";
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Ensure fly exists
if ! command -v fly >/dev/null 2>&1; then
  echo "Error: fly CLI not found. Install with: brew install flyctl" >&2
  exit 1
fi

# Choose env file if not provided
if [ -z "$ENV_FILE" ]; then
  if [ -f "${BACKEND_DIR}/.env" ]; then
    ENV_FILE="${BACKEND_DIR}/.env"
  elif [ -f "${REPO_ROOT}/.env" ]; then
    ENV_FILE="${REPO_ROOT}/.env"
  else
    echo "Error: No .env file found. Provide --env-file PATH" >&2
    exit 1
  fi
fi

# Infer app from fly.toml if not provided
if [ -z "$APP" ] && [ -f "${BACKEND_DIR}/fly.toml" ]; then
  # Extract: app = 'name'
  APP=$(sed -n "s/^app *= *'\([^']*\)'.*$/\1/p" "${BACKEND_DIR}/fly.toml" | head -n1 || true)
fi

if [ -z "$APP" ]; then
  echo "Error: --app not provided and app not found in backend/fly.toml" >&2
  exit 1
fi

# Allowlist regex (only used when --all is not specified)
ALLOWLIST_REGEX='^(OPENAI_API_KEY|OPENAI_MODEL|DATABASE_URL|REDIS_URL|BROKER_URL|CELERY_RESULT_BACKEND|ENV|POPPLER_PATH|PIPELINE_LOG_LEVEL|PARSER_LOG_LEVEL|DOC_CLS_LOG_LEVEL|LOG_LEVEL|S3_ENDPOINT|S3_ACCESS_KEY|S3_SECRET_KEY|S3_BUCKET)$'

echo "Using app: $APP"
echo "Using env file: $ENV_FILE"
if [ "$PUSH_ALL" -eq 0 ]; then
  echo "Using allowlist (override with --all)"
fi

COUNT=0
# Read .env line-by-line
# - Strip CRs and surrounding whitespace
# - Ignore comments and blank lines
# - Drop leading 'export '
# - Keep everything after first '=' as value (supports '=' in value)
while IFS= read -r line || [ -n "$line" ]; do
  # Remove CR at EOL if present
  line=${line%$'\r'}
  # Trim whitespace
  line=$(printf '%s' "$line" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
  # Skip comments/blank
  [ -z "$line" ] && continue
  case "$line" in \#*) continue ;; esac
  # Drop leading export
  case "$line" in export\ *) line=${line#export } ;; esac
  # Must contain '='
  case "$line" in *"="*) ;; *) continue ;; esac

  key=${line%%=*}
  val=${line#*=}

  # Strip quotes around the entire value if present
  if printf '%s' "$val" | grep -Eq '^".*"$'; then
    val=${val#""}
    val=${val%""}
  elif printf '%s' "$val" | grep -Eq "^'.*'$"; then
    val=${val#\'}
    val=${val%\'}
  fi

  # Filter by allowlist if not --all
  if [ "$PUSH_ALL" -eq 0 ]; then
    if ! printf '%s' "$key" | grep -Eq "$ALLOWLIST_REGEX"; then
      continue
    fi
  fi

  # Set secret (one by one to avoid array usage and preserve spaces)
  fly secrets set "$key=$val" -a "$APP"
  COUNT=$((COUNT+1))

done < "$ENV_FILE"

if [ "$COUNT" -eq 0 ]; then
  echo "No secrets were set (check allowlist or env file)." >&2
  exit 1
fi

echo "Done. Set $COUNT secret(s) on Fly app $APP."
