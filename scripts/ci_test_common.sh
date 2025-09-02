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