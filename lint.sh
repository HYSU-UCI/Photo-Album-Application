#!/bin/bash
# This is modified from https://github.com/pwndbg/pwndbg/blob/dev/lint.sh

set -o errexit

help_and_exit() {
    echo "Usage: ./lint.sh [-f|--format]"
    echo "  -f,  --format         format code instead of just checking the format"
    exit 1
}

if [[ $# -gt 1 ]]; then
    help_and_exit
fi

FORMAT=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -f | --format)
            FORMAT=1
            shift
            ;;
        *)
            help_and_exit
            ;;
    esac
done

LINT_PYTHON_FILES=(
    "./frontend"
    "./backend"
)

if [[ $FORMAT == 1 ]]; then
    ruff check "${LINT_PYTHON_FILES[@]}" --fix
    isort "${LINT_PYTHON_FILES[@]}"
    black "${LINT_PYTHON_FILES[@]}"
else
    ruff check "${LINT_PYTHON_FILES[@]}"
    isort --check-only --diff "${LINT_PYTHON_FILES[@]}"
    black --check --diff "${LINT_PYTHON_FILES[@]}"
fi

echo "Linting done!"