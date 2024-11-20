#!/bin/bash
set -e # Exit with nonzero exit code if anything fails
sh scripts/clean_imports.sh
mypy . --config-file .vscode/.mypy.ini

echo "Type-Checking passed successfully!"