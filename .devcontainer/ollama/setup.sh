#!/usr/bin/env bash
# Like .devcontainer/setup.sh, but for the local Ollama + Qwen3 variant:
# creates the conda env and installs the project (via the shared script),
# then installs Ollama and ollmcp, and pulls the default model. Runs once,
# on codespace creation.
set -euo pipefail

bash "$(dirname "$0")/../setup.sh"

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# ollmcp needs mcp~=2.1 while ersilia-mcp's fastmcp needs mcp==1.28.1, so
# the two can't share an env.
echo "Installing the ollmcp MCP client into its own conda env..."
if ! conda env list | grep -qE "^ollmcp\s"; then
  conda create -y -n ollmcp python=3.12
fi
conda run --no-capture-output -n ollmcp pip install ollmcp==0.35.1

echo "Pulling qwen3:1.7b (one-time, ~1.4GB)..."
ollama serve &
OLLAMA_PID=$!
for _ in $(seq 1 15); do
  curl -sf --max-time 5 http://127.0.0.1:11434 >/dev/null 2>&1 && break
  sleep 2
done
ollama pull qwen3:1.7b
kill "${OLLAMA_PID}"

echo "Resolving .mcp.json for ollmcp..."
bash "$(dirname "$0")/resolve-mcp-config.sh"

# ollmcp finds .mcp.json by looking in the current directory, so the alias
# runs from the repo root in a subshell.
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# Replace rather than skip an existing alias, so a changed model takes effect.
sed -i '/alias ersilia-chat=/d' "${HOME}/.bashrc"
echo "alias ersilia-chat='(cd \"${REPO_ROOT}\" && conda run --no-capture-output -n ollmcp ollmcp --model qwen3:1.7b)'" >>"${HOME}/.bashrc"

echo "Setup complete. In a new terminal, run:"
echo "  ersilia-chat"
echo "For better tool-calling quality (needs more RAM), see the qwen3:4b"
echo "upgrade instructions in docs/mcp_setup/ollama.md."
