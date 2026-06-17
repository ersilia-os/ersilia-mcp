## Setup

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
# for local development
pip install -e ".[dev]"
```

Logs can be found in ersilia-mcp/logs/ersilia-mcp.log

## Register
### Claude Code

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

## Linter
```bash
ruff format
```

## Tests
```bash
pytest -v
```
