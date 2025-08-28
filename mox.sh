#!/bin/bash
# Unix launcher for mox.py using isolated venv in /venv/venv/

# Ensure venv
python3 "$(pwd)/venv/venv.py"
if [ $? -ne 0 ]; then exit $?; fi

# Add venv/bin to PATH temporarily
export PATH="$(pwd)/venv/venv/bin:$PATH"

# Run mox
"$(pwd)/venv/venv/bin/python3" "$(pwd)/scripts/mox.py" "$@"
