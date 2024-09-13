#!/bin/bash
set -e # Exit with nonzero exit code if anything fails
ruff check --config .vscode/ruff.toml .

echo "Linting passed successfully!"