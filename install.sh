#!/usr/bin/env bash
# Install the pre-built WorkBuddy expert teams (macOS / Linux).
# Requires python3 (present by default on macOS/Linux; any Python 3.8+ works).
set -euo pipefail
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python || true)"
[ -z "$PY" ] && { echo "python3 not found; please install Python 3 first" >&2; exit 1; }
exec "$PY" scripts/install.py "$@"
