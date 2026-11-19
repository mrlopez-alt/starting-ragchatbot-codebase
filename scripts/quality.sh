#!/bin/bash
# Run all code quality checks without modifying files.
# Exits non-zero if any check fails (suitable for CI / pre-push).
cd "$(dirname "$0")/.."

status=0

echo "==> Checking import order (isort)..."
uv run isort --check-only --diff backend main.py || status=1

echo "==> Checking formatting (black)..."
uv run black --check --diff backend main.py || status=1

echo "==> Linting (flake8)..."
uv run flake8 backend main.py || status=1

if [ $status -eq 0 ]; then
    echo "All quality checks passed."
else
    echo "Some quality checks failed. Run ./scripts/format.sh to auto-fix formatting."
fi
exit $status
