#!/bin/bash
set -e # Exit with nonzero exit code if anything fails
sh scripts/clean_imports.sh
ruff check --config .vscode/ruff.toml .

echo "Linting passed successfully!"