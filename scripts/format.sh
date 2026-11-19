#!/bin/bash
# Auto-format the codebase: sort imports (isort) and format code (black).
set -e
cd "$(dirname "$0")/.."

echo "==> Sorting imports (isort)..."
uv run isort backend main.py

echo "==> Formatting code (black)..."
uv run black backend main.py

echo "Formatting complete."
