#!/bin/bash
# Unix launcher for mox.py using isolated venv in /venv/venv/

set -euo pipefail

# Folder discovery – and immediately cd there so all scripts see repo root as cwd
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" >/dev/null 2>&1 && pwd -P)"
cd "$SCRIPT_DIR"

# Ensure venv – use the venv's own python3 if it already exists so that
# Xcode's stripped PATH (no Homebrew) never blocks pre/post-build phases.
VENV_PYTHON="$SCRIPT_DIR/venv/venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    python3 "$SCRIPT_DIR/venv/venv.py"
fi

# Add venv/bin to PATH temporarily
export PATH="$SCRIPT_DIR/venv/venv/bin:$PATH"

# Run mox
exec "$VENV_PYTHON" "$SCRIPT_DIR/scripts/mox.py" "$@"
