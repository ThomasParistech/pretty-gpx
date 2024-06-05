#!/bin/bash
ruff check --config .vscode/ruff.toml --fix --select F401 .
ruff check --config .vscode/ruff.toml --fix --select I .
