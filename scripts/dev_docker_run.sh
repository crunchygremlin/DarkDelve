#!/usr/bin/env bash
set -euo pipefail

# Dev helper to run docker compose with host networking on Linux
# If on macOS/Windows, host networking behaves differently; use the compose file as-is.

if [ "$(uname)" == "Linux" ]; then
  echo "Running docker-compose with host network for better Ollama host access"
  docker compose up --build
else
  echo "Non-Linux host detected; use default docker compose or run Ollama on host and set LOCAL_LLM_ENDPOINT"
  docker compose up --build
fi
