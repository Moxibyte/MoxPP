#!/bin/bash
# Unix launcher for mox.py using isolated venv in /venv/venv/

set -euo pipefail

# Folder discovery
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" >/dev/null 2>&1 && pwd -P)"

# Ensure venv
python3 "$SCRIPT_DIR/venv/venv.py"
if [ $? -ne 0 ]; then exit $?; fi

# Add venv/bin to PATH temporarily
export PATH="$SCRIPT_DIR/venv/venv/bin:$PATH"

# Run mox
exec "$SCRIPT_DIR/venv/venv/bin/python3" "$SCRIPT_DIR/scripts/mox.py" "$@"
