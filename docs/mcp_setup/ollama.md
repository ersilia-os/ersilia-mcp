# Setting Up the Ersilia MCP Server with Ollama + Qwen3

This is a fully local, offline, genuinely free way to use the Ersilia model tools: [Ollama](https://ollama.com) runs a small [Qwen3](https://ollama.com/library/qwen3) model on CPU, and [`ollmcp`](https://github.com/jonigl/mcp-client-for-ollama) bridges that local model to the Ersilia MCP server. No API key, no account, and no hosted CLI required.

## Step 1: Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

See the [official installation guide](https://ollama.com/download) for other platforms. Start the daemon with `ollama serve` (or let its systemd unit handle that on a real machine).

## Step 2: Pull the Default Model

```bash
ollama pull qwen3:1.7b
```

`qwen3:1.7b` is ~1.4GB to download and needs ~4GB of resident RAM — the default here because it's the lighter, safer choice on a shared or constrained machine.

## Step 3 (Optional): Upgrade to a Larger Model

```bash
ollama pull qwen3:4b
```

`qwen3:4b` is ~2.5GB / ~6GB RAM and noticeably better at tool-calling and reasoning than `qwen3:1.7b`. The tradeoff is explicit: better quality for more RAM. If you pull this, use `--model qwen3:4b` instead of `qwen3:1.7b` in Step 6.

## Step 4: Install ollmcp (in its own isolated environment)

```bash
conda create -y -n ollmcp python=3.12
conda run --no-capture-output -n ollmcp pip install ollmcp==0.35.1
```

Don't install `ollmcp` into the `ersilia-mcp` env. It depends on `mcp~=2.1.x`, which conflicts with this repo's own `mcp==1.28.1` pin (needed by `fastmcp`): installing it there silently upgrades the shared `mcp` package and breaks the Ersilia MCP server itself. A separate env avoids that entirely. `ollmcp` needs Python 3.11 or newer.

## Step 5: Generate ollmcp's Server Config

```bash
bash .devcontainer/ollama/generate-mcp-config.sh
```

`.mcp.json`'s `command` field uses `${CONDA_EXE:-conda}` — a Claude-Code-specific expansion syntax that `ollmcp` doesn't understand (it would try to literally exec a program named `${CONDA_EXE:-conda}` and fail). This script resolves that value with native bash expansion and writes a usable copy to `~/.config/ersilia-mcp/ollama-mcp-servers.json` by default.

## Step 6: Run It

From the repo root:

```bash
conda run --no-capture-output -n ollmcp ollmcp --servers-json ~/.config/ersilia-mcp/ollama-mcp-servers.json --model qwen3:1.7b
```

## Step 7: Verify

Inside the `ollmcp` TUI, confirm the Ersilia tools (`search_model`, `fetch_model`, `predict`, etc.) show up as connected.

## Devcontainer / Codespaces

This repo ships a `.devcontainer/ollama/devcontainer.json` config that automates Steps 1, 2, 4, and 5 — it installs Ollama, pulls `qwen3:1.7b`, installs `ollmcp` into its own `ollmcp` conda env, and generates the server config on container creation, and keeps the Ollama daemon running on every attach. Pick "ersilia-mcp-local-llm" from the Codespaces config picker to use it. Step 6 (launching `ollmcp`) is the one command still left for you to run interactively.

That config also sets `"hostRequirements": {"cpus": 4, "memory": "16gb"}`. This is sized for the Step 3 upgrade path (`qwen3:4b` at ~6GB resident) running concurrently with the Ersilia/Isaura containers that docker-in-docker brings up, not just the lighter default model — so upgrading to `qwen3:4b` inside an already-provisioned Codespace doesn't unexpectedly exceed what the machine was sized for.
