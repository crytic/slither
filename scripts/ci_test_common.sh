#!/usr/bin/env bash

# Common setup for CI test scripts
# Use UV_RUN if set (for CI), otherwise run directly (for local dev)
RUN="${UV_RUN:-}"

# Export wrapper functions for commonly used commands
slither() {
    $RUN slither "$@"
}

slither-check-upgradeability() {
    $RUN slither-check-upgradeability "$@"
}

slither-check-kspec() {
    $RUN slither-check-kspec "$@"
}

slither-check-erc() {
    $RUN slither-check-erc "$@"
}

slither-flat() {
    $RUN slither-flat "$@"
}

slither-simil() {
    $RUN slither-simil "$@"
}

slither-interface() {
    $RUN slither-interface "$@"
}

slither-find-paths() {
    $RUN slither-find-paths "$@"
}

slither-prop() {
    $RUN slither-prop "$@"
}

solc-select() {
    $RUN solc-select "$@"
}

python() {
    $RUN python "$@"
}

pip() {
    $RUN pip "$@"
}

# solc is installed by solc-select outside the venv, so we need special handling
solc() {
    # If we're in CI with UV_RUN set, we need to ensure solc-select's bin is in PATH
    if [ -n "$UV_RUN" ]; then
        # Get the current solc version from solc-select
        # Use command to avoid calling our wrapper function
        SOLC_VERSION=$(command $RUN solc-select versions 2>/dev/null | grep "(current" | cut -d' ' -f1)
        
        # Get the actual virtual environment path from uv
        # When uv run executes, it sets up a venv but VIRTUAL_ENV might not be set in our shell context
        UV_VENV=$(command $RUN python -c "import sys; print(sys.prefix)" 2>/dev/null)
        
        # Determine where solc-select would have installed the binary
        if [ -n "$UV_VENV" ] && [ -d "$UV_VENV/.solc-select" ]; then
            # uv virtual environment exists and has solc-select
            SOLC_BASE="$UV_VENV/.solc-select"
        elif [ -n "$VIRTUAL_ENV" ]; then
            # VIRTUAL_ENV is set in the environment
            SOLC_BASE="$VIRTUAL_ENV/.solc-select"
        else
            # Fall back to HOME directory
            SOLC_BASE="$HOME/.solc-select"
        fi
        
        # Try multiple possible locations for the solc binary
        # Different systems may have different structures
        if [ -f "$SOLC_BASE/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" ]; then
            # MacOS/local structure: artifacts/solc-X.Y.Z/solc-X.Y.Z
            "$SOLC_BASE/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" "$@"
        elif [ -f "$SOLC_BASE/artifacts/solc-$SOLC_VERSION" ]; then
            # Linux/CI structure: artifacts/solc-X.Y.Z (binary directly)
            "$SOLC_BASE/artifacts/solc-$SOLC_VERSION" "$@"
        elif [ -f "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" ]; then
            # Fallback to HOME directory - MacOS/local structure
            "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" "$@"
        elif [ -f "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION" ]; then
            # Fallback to HOME directory - Linux/CI structure (binary directly)
            "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION" "$@"
        else
            echo "Error: solc-$SOLC_VERSION not found in solc-select artifacts" >&2
            echo "VIRTUAL_ENV: ${VIRTUAL_ENV:-not set}" >&2
            echo "UV_VENV: ${UV_VENV:-not found}" >&2
            echo "HOME: $HOME" >&2
            echo "SOLC_BASE: $SOLC_BASE" >&2
            echo "Searched locations:" >&2
            echo "  - $SOLC_BASE/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" >&2
            echo "  - $SOLC_BASE/artifacts/solc-$SOLC_VERSION" >&2
            echo "  - $HOME/.solc-select/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" >&2
            echo "  - $HOME/.solc-select/artifacts/solc-$SOLC_VERSION" >&2
            return 1
        fi
    else
        # Local development - use solc directly
        command solc "$@"
    fi
}

# Export the functions
export -f slither
export -f slither-check-upgradeability
export -f slither-check-kspec
export -f slither-check-erc
export -f slither-flat
export -f slither-simil
export -f slither-interface
export -f slither-find-paths
export -f slither-prop
export -f solc-select
export -f python
export -f pip
export -f solc