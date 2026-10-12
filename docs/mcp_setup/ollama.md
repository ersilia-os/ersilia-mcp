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

`qwen3:4b` is ~2.5GB / ~6GB RAM and noticeably better at tool-calling and reasoning than `qwen3:1.7b`. The tradeoff is explicit: better quality for more RAM. If you pull this, use `--model qwen3:4b` instead of `qwen3:1.7b` in Step 5.

## Step 4: Install ollmcp

```bash
pip install --upgrade ollmcp
# or: uv tool install --upgrade ollmcp
```

## Step 5: Run It

From the repo root:

```bash
ollmcp --servers-json .mcp.json --model qwen3:1.7b
```

`.mcp.json` is already in the `mcpServers` shape `ollmcp` expects, so it's passed straight through — no conversion needed.

## Step 6: Verify

Inside the `ollmcp` TUI, confirm the Ersilia tools (`search_model`, `fetch_model`, `predict`, etc.) show up as connected.

## Devcontainer / Codespaces

This repo ships a `.devcontainer/ollama/devcontainer.json` config that automates Steps 1, 2, and 4 — it installs Ollama, pulls `qwen3:1.7b`, and installs `ollmcp` on container creation, and keeps the Ollama daemon running on every attach. Pick "ersilia-mcp-qwen" from the Codespaces config picker to use it. Step 5 (launching `ollmcp`) is the one command still left for you to run interactively.

That config also sets `"hostRequirements": {"cpus": 4, "memory": "16gb"}`. This is sized for the Step 3 upgrade path (`qwen3:4b` at ~6GB resident) running concurrently with the Ersilia/Isaura containers that docker-in-docker brings up, not just the lighter default model — so upgrading to `qwen3:4b` inside an already-provisioned Codespace doesn't unexpectedly exceed what the machine was sized for.
