#!/usr/bin/env bash
set -euo pipefail

# Dev runner for the game. Sets a default LOCAL_LLM_ENDPOINT if not provided.
: "${LOCAL_LLM_ENDPOINT:=http://127.0.0.1:11434/api/generate}"
export LOCAL_LLM_ENDPOINT

echo "Using LOCAL_LLM_ENDPOINT=$LOCAL_LLM_ENDPOINT"

# Activate venv if present
if [ -f .venv/bin/activate ]; then
  echo "Activating .venv"
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

python3 main.py
