## Setup

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
# for local development
pip install -e ".[dev]"
```

## Using the MCP server with the Claude CLI
### Auto registering

The repo ships a project-scoped [`.mcp.json`](.mcp.json) that'll automatically configure Claude to launch this local mcp server over stdio:

```json
{
  "mcpServers": {
    "ersilia-mcp": {
      "command": "${CONDA_EXE:-conda}",
      "args": ["run", "--no-capture-output", "-n", "ersilia-mcp", "ersilia-mcp"]
    }
  }
}
```
Note:`--no-capture-output` is required: without it `conda run` buffers stdout and corrupts the stdio JSON-RPC stream, so the MCP handshake fails.

You'll need to run `claude` to approve this new mcp server.

Run the following to verify the server is running properly:
```bash
claude mcp list
```

You should see something like:
```bash
ersilia-mcp: ${CONDA_EXE:-conda} run --no-capture-output -n ersilia-mcp ersilia-mcp - ✔ Connected
```

### Registering manually

To register manually instead (e.g. a different env name), the equivalent is:
```bash
claude mcp add ersilia-mcp -- conda run --no-capture-output -n ersilia-mcp ersilia-mcp
```

Run the following to verify the server is running properly:
```bash
claude mcp list
```

You should see something like:
```bash
ersilia-mcp: conda run --no-capture-output -n ersilia-mcp ersilia-mcp - ✔ Connected
```

If you're using the Claude Code for VS Code extension, you can also type `/mcp` in the chatbox.

## Starting the server locally

After registering, Claude should automatically start the MCP server as a subprocess.
You can check this by running `ps aux | grep ersilia-mcp` or by running `/mcp` in the chatbox. Logs can be found in ersilia-mcp/logs/ersilia-mcp.log

If you don't see a running process or if `/mcp` is showing an error, you can debug this by starting the server manually:
```bash
conda activate ersilia-mcp
ersilia-mcp
```

## Linter
```bash
ruff format
```

## Running tests locally
```bash
# Skip integration tests to avoid corrupting your local env
pytest -v -m "not integration"
```

## Debugging Ersilia operations
Locally fetched/served models are stored in the `~/eos/` directory.

To manually check which models are fetched, check `~/eos/repository/`.
To manually check which models are served, check `~/eos/sessions/`.

Note: Since we're using the ersilia python package, the ersilia CLI should also be installed in your conda environment.
