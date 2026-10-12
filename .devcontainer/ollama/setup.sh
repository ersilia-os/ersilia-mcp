#!/usr/bin/env bash
# Like .devcontainer/setup.sh, but for the local Ollama + Qwen3 variant:
# creates the conda env and installs the project (via the shared script),
# then installs Ollama and ollmcp, and pulls the default model. Runs once,
# on codespace creation.
set -euo pipefail

bash "$(dirname "$0")/../setup.sh"

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "Installing the ollmcp MCP client (isolated Poetry env, separate from"
echo "ersilia-mcp's own dependencies)..."
OLLMCP_ENV_DIR="$(dirname "$0")/ollmcp-env"
(cd "$OLLMCP_ENV_DIR" && conda run --no-capture-output -n ersilia-mcp poetry lock)
(cd "$OLLMCP_ENV_DIR" && conda run --no-capture-output -n ersilia-mcp poetry install)

echo "Pulling qwen3:1.7b (one-time, ~1.4GB)..."
ollama serve &
OLLAMA_PID=$!
for _ in $(seq 1 15); do
  curl -sf --max-time 5 http://127.0.0.1:11434 >/dev/null 2>&1 && break
  sleep 2
done
ollama pull qwen3:1.7b
kill "${OLLAMA_PID}"

echo "Generating ollmcp-compatible MCP server config..."
bash "$(dirname "$0")/generate-mcp-config.sh"

echo "Setup complete. From the repo root, run:"
echo "  cd .devcontainer/ollama/ollmcp-env && poetry run ollmcp --servers-json ~/.config/ersilia-mcp/ollama-mcp-servers.json --model qwen3:1.7b"
echo "For better tool-calling quality (needs more RAM), see the qwen3:4b"
echo "upgrade instructions in docs/mcp_setup/ollama.md."
