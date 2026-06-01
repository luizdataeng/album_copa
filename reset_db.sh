#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

rm -f "$SCRIPT_DIR/backend/album.sqlite3"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/backend/seed.py"

echo "Database reset complete."
