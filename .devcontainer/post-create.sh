#!/usr/bin/env bash
set -euo pipefail

# Repo-Wurzel (WORKSPACE_FOLDER ist in Devcontainers meist gesetzt, sonst fallback auf PWD)
REPO_ROOT="${WORKSPACE_FOLDER:-$PWD}"

# Caches unterhalb des Repos -> immer schreibbar
export XDG_CACHE_HOME="$REPO_ROOT/.cache"
export PRE_COMMIT_HOME="$XDG_CACHE_HOME/pre-commit"
export PIP_CACHE_DIR="$XDG_CACHE_HOME/pip"

mkdir -p "$PIP_CACHE_DIR" "$PRE_COMMIT_HOME"

echo "[post-create] installiere Dev-Abhängigkeiten..."
pip install -e .[dev]

echo "[post-create] installiere pre-commit Hooks..."
pre-commit install --install-hooks || true

echo "[post-create] fertig!"
