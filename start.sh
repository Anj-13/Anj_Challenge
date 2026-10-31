#!/bin/bash

# Sets up the backend on first run, then starts the API.
# Dependencies are only installed when requirements.txt has changed.

requirements_file="requirements.txt"
installed_file="venv/installed-requirements.txt"

fail() {
    echo "ERROR: $1" >&2
    exit 1
}

# Git Bash on Windows keeps the venv's python in a different folder
find_venv_python() {
    if [ -x venv/bin/python ]; then
        echo "venv/bin/python"
    elif [ -x venv/Scripts/python.exe ]; then
        echo "venv/Scripts/python.exe"
    fi
}

cd "$(dirname "${BASH_SOURCE[0]}")/backend" || fail "Could not find the backend folder."

[ -f "$requirements_file" ] || fail "Could not find backend/$requirements_file."

# Check if the virtual environment exists
if [ -z "$(find_venv_python)" ]; then
    python_command=""
    for candidate in python3 python; do
        if "$candidate" --version >/dev/null 2>&1; then
            python_command="$candidate"
            break
        fi
    done
    [ -n "$python_command" ] || fail "Python was not found. Install Python 3 from https://www.python.org/downloads/ and try again."

    echo "Virtual environment not found. Creating..."
    "$python_command" -m venv venv || fail "Could not create the virtual environment. On Debian or Ubuntu, install the python3-venv package first."
fi

venv_python="$(find_venv_python)"

# Install requirements if they are missing or out of date
if ! cmp -s "$requirements_file" "$installed_file"; then
    echo "Installing python dependencies..."
    "$venv_python" -m pip install -r "$requirements_file" || fail "Could not install the dependencies. Check your internet connection and try again."
    cp "$requirements_file" "$installed_file"
fi

echo "Starting the API at http://127.0.0.1:8000. Open frontend/index.html in your browser, and press Ctrl+C to stop."
"$venv_python" main.py
