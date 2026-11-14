#!/usr/bin/env bash
set -e

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# Find the first working Python 3 interpreter.
find_python() {
    for candidate in "py -3" python3 python; do
        # Unquoted on purpose so "py -3" splits into command + argument.
        if $candidate -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)' >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# Use the repository's virtual environment without requiring activation.
if [ ! -f .venv/Scripts/python.exe ] && [ ! -x .venv/bin/python ]; then
    PYTHON=$(find_python) || { echo "Python 3 is required." >&2; exit 1; }
    $PYTHON -m venv .venv
fi

if [ -f .venv/Scripts/python.exe ]; then
    VENV_PYTHON=./.venv/Scripts/python.exe
else
    VENV_PYTHON=./.venv/bin/python
fi

# Older Pythons ship an old pip; upgrading helps it find compatible packages.
"$VENV_PYTHON" -m pip install --upgrade pip || true
"$VENV_PYTHON" -m pip install pre-commit
"$VENV_PYTHON" -m pre_commit install --install-hooks
