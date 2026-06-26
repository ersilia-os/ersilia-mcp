## Setup

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
# for local development
pip install -e ".[dev]"
```

## Using the MCP server with Claude Desktop
### Register

`claude mcp add` needs the absolute path to the entry point, and it does not
inherit your activated conda environment. Find it and register:
```bash
conda activate ersilia-mcp
which ersilia-mcp   # e.g. /Users/you/miniconda3/envs/ersilia-mcp/bin/ersilia-mcp

claude mcp add ersilia-mcp "$(which ersilia-mcp)"
```

You can check to see if it's connected properly by running:
```bash
claude mcp list
```

You should see something like:
```bash
ersilia-mcp: /Users/you/miniconda3/envs/ersilia-mcp/bin/ersilia-mcp  - ✓ Connected
```

If you're using the VSCode extension, you can also type `/mcp` in the chatbox.

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
