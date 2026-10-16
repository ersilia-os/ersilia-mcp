#!/usr/bin/env bash
# Rewrites .mcp.json in place, resolving the Claude-specific
# `${CONDA_EXE:-conda}` command into a literal value -- ollmcp doesn't support
# that expansion syntax. Marks the file skip-worktree so the machine-specific
# path isn't accidentally committed. Run from the repo root.
set -euo pipefail

RESOLVED_CONDA="${CONDA_EXE:-conda}"

python3 - "$RESOLVED_CONDA" <<'PY'
import json, sys

resolved_conda = sys.argv[1]
with open(".mcp.json") as f:
    config = json.load(f)
for server in config["mcpServers"].values():
    if server.get("command") == "${CONDA_EXE:-conda}":
        server["command"] = resolved_conda
with open(".mcp.json", "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PY

git update-index --skip-worktree .mcp.json
echo "Resolved .mcp.json command to ${RESOLVED_CONDA} (marked skip-worktree)"
