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
        # Use the specific solc binary from solc-select's artifacts
        if [ -f "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" ]; then
            "$HOME/.solc-select/artifacts/solc-$SOLC_VERSION/solc-$SOLC_VERSION" "$@"
        else
            echo "Error: solc-$SOLC_VERSION not found in solc-select artifacts" >&2
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