#!/usr/bin/env bash
# Like .devcontainer/setup.sh, but for the local Ollama + Qwen3 variant:
# creates the conda env and installs the project (via the shared script),
# then installs Ollama and ollmcp, and pulls the default model. Runs once,
# on codespace creation.
set -euo pipefail

bash "$(dirname "$0")/../setup.sh"

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "Installing the ollmcp MCP client..."
conda run --no-capture-output -n ersilia-mcp pip install --upgrade ollmcp

echo "Pulling qwen3:1.7b (one-time, ~1.4GB)..."
ollama serve &
OLLAMA_PID=$!
for _ in $(seq 1 15); do
  curl -sf --max-time 5 http://127.0.0.1:11434 >/dev/null 2>&1 && break
  sleep 2
done
ollama pull qwen3:1.7b
kill "${OLLAMA_PID}"

echo "Setup complete. From the repo root, run:"
echo "  ollmcp --servers-json .mcp.json --model qwen3:1.7b"
