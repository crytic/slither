#!/usr/bin/env bash

# Common setup for CI test scripts
# In CI, activate the virtual environment so all tools are in PATH
# In local development, assume the environment is already set up

if [ -n "$UV_RUN" ]; then
    # CI environment - activate the virtual environment created by uv
    # Find the project root (where .venv is located)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    
    # Activate the virtual environment
    # This puts all installed tools in PATH
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi
    
    # Set VIRTUAL_ENV for solc-select to use
    # This ensures solc binaries are installed to .venv/.solc-select
    export VIRTUAL_ENV="$PROJECT_ROOT/.venv"
fi

# Now all commands work directly without wrappers
# slither, solc-select, python, etc. are all in PATH