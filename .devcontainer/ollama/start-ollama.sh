#!/usr/bin/env bash
# Bring up the local Ollama daemon so ollmcp has something to connect to.
# Runs on every attach, so it must be idempotent and must not fail the
# attach.
set -uo pipefail

if curl -sf --max-time 5 http://127.0.0.1:11434 >/dev/null 2>&1; then
  echo "Ollama already running."
  echo "To chat with the Ersilia tools, from the repo root run:"
  echo "  cd .devcontainer/ollama/ollmcp-env && poetry run ollmcp --servers-json ~/.config/ersilia-mcp/ollama-mcp-servers.json --model qwen3:1.7b"
  exit 0
fi

echo "Starting Ollama..."
nohup ollama serve >/tmp/ollama.log 2>&1 &
disown

for _ in $(seq 1 10); do
  if curl -sf --max-time 5 http://127.0.0.1:11434 >/dev/null 2>&1; then
    echo "Ollama ready on port 11434."
    echo "To chat with the Ersilia tools, from the repo root run:"
    echo "  cd .devcontainer/ollama/ollmcp-env && poetry run ollmcp --servers-json ~/.config/ersilia-mcp/ollama-mcp-servers.json --model qwen3:1.7b"
    exit 0
  fi
  sleep 2
done

echo "Ollama did not become reachable. Check 'ollama serve' for status."
exit 0
