#!/usr/bin/env bash
# Resolves the Claude-specific `${VAR:-default}` expansion in .mcp.json's
# command field into a literal value -- ollmcp (unlike Claude Code) doesn't
# support that expansion syntax and would otherwise try to exec a program
# literally named "${CONDA_EXE:-conda}". Run from the repo root.
set -euo pipefail

OUT="${1:-$HOME/.config/ersilia-mcp/ollama-mcp-servers.json}"
mkdir -p "$(dirname "$OUT")"
RESOLVED_CONDA="${CONDA_EXE:-conda}"

python3 - "$OUT" "$RESOLVED_CONDA" <<'PY'
import json, sys

out_path, resolved_conda = sys.argv[1], sys.argv[2]
with open(".mcp.json") as f:
    config = json.load(f)
for server in config["mcpServers"].values():
    if server.get("command") == "${CONDA_EXE:-conda}":
        server["command"] = resolved_conda
with open(out_path, "w") as f:
    json.dump(config, f, indent=2)
PY

echo "Wrote ${OUT}"
