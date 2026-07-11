## Setup

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
# for local development
pip install -e ".[dev]"
```

## Dependency Management

This project uses Poetry and a lockfile to ensure consistent dependency resolution across different environments (CI, local dev, different OS runners).

### Generating the lockfile

When you add or update dependencies in `pyproject.toml`, regenerate the lockfile:

```bash
pip install poetry
poetry lock
```

This creates `poetry.lock` with all transitive dependencies pinned to exact versions.

### Using the lockfile

**For development:** Install from the lockfile to match CI:
```bash
poetry install --all-extras
```

### When to regenerate

- After updating `pyproject.toml`
- When CI fails with dependency resolution errors
- Periodically (e.g., quarterly) to pick up security patches

## Using the MCP server with Claude Code

### Auto registration

The repo ships a project-scoped [`.mcp.json`](.mcp.json) that automatically configures
Claude to launch the MCP server over stdio:

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

Verify the server is running:
```bash
claude mcp list
```

You should see `ersilia-mcp: ... - ✔ Connected`.

If you're using the Claude Code VS Code extension, you can also type `/mcp` in the chatbox.

**Caveat:** If you have an older local registration (from `claude mcp add`), it may take
precedence. To rely on the committed `.mcp.json`, remove the local registration:
```bash
claude mcp remove ersilia-mcp
```

### Manual registration

To register manually (e.g. for a different environment name):
```bash
claude mcp add ersilia-mcp -- conda run --no-capture-output -n ersilia-mcp ersilia-mcp
```

## Starting the server locally

After registering, Claude should automatically start the MCP server as a subprocess.
You can check this by running `ps aux | grep ersilia-mcp` or by running `/mcp` in the chatbox. Logs can be found in ersilia-mcp/logs/ersilia-mcp.log

If you don't see a running process or if `/mcp` is showing an error, you can debug this by starting the server manually:
```bash
conda activate ersilia-mcp
ersilia-mcp
```

## Linting and Code Quality

Run ruff to check and format code:
```bash
ruff check .
ruff format .
```

## Tests

The test suite is split into two categories:

**Unit tests** (fast, safe, run offline):
```bash
pytest -v -m "not integration"
```

These test the MCP tools and utilities with mocked Ersilia API calls. Safe to run locally without side effects.

**Integration tests** (slower, hit real APIs, mark with `@pytest.mark.integration`):
```bash
pytest -v -m integration
```

These call the live Ersilia Model Hub APIs to validate search and fetch operations against real data. Note: fetching models can populate `~/eos/repository/`, so clean up afterwards if needed.

## CI/CD

A [GitHub Action](.github/workflows/ci.yml) runs on every push to `main` and on pull requests.

## Debugging Ersilia operations
Locally fetched/served models are stored in the `~/eos/` directory.

To manually check which models are fetched, check `~/eos/repository/`.
To manually check which models are served, check `~/eos/sessions/`.

Note: Since we're using the ersilia python package, the ersilia CLI should also be installed in your conda environment.
