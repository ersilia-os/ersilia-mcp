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

## Client Setup & Registration

This MCP server has been tested mainly on Claude (specifically using Claude Code), but it can be used with any model provider or host (Gemini, ChatGPT, Claude) that supports local stdio MCP servers.

**Note on Claude Code:** This repository is set up to be automatically configured with Claude Code out of the box. It includes a project-scoped `.mcp.json` configuration file so that when you run Claude Code in this workspace, the Ersilia MCP server is registered and started automatically.

Currently, we only have dedicated setup and registration documentation for:
- [Claude Code Setup Guide](docs/mcp_setup/claude_code.md)
- [Gemini Setup Guide](docs/mcp_setup/gemini.md)

We would love to receive documentation updates and setup guides for other MCP clients and platforms. If you have successfully integrated this server with other environments, please feel free to submit a pull request with new client guides! See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### Claude Code Registration Summary

For quick reference, the repository ships a project-scoped [`.mcp.json`](.mcp.json) that automatically configures Claude Code to launch the MCP server over stdio.

Verify the server is running:
```bash
claude mcp list
```

You should see `ersilia-mcp: ... - ✔ Connected`.

For a full step-by-step walkthrough of automatic vs. manual registration, caveats, and extension setups, refer to the [Claude Code Setup Guide](docs/mcp_setup/claude_code.md).

## Starting the server locally

After registering, Claude should automatically start the MCP server as a subprocess.
You can check this by running `ps aux | grep ersilia-mcp` or by running `/mcp` in the chatbox. Logs can be found in `$HOME/eos/mcp/logs`.

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

These call the live Ersilia Model Hub APIs to validate the full model lifecycle (search, fetch, serve, generate_inputs, predict, close, delete) against real data. Note: fetching models can populate `~/eos/repository/`, so clean up afterwards if needed.

## CI/CD

A [GitHub Action](.github/workflows/ci.yml) runs on every push to `main` and on pull requests.

## Debugging Ersilia operations
Locally fetched/served models are stored in the `~/eos/` directory.

To manually check which models are fetched, check `~/eos/repository/`.
To manually check which models are served, check `~/eos/sessions/`.

Note: Since we're using the ersilia python package, the ersilia CLI should also be installed in your conda environment. See [these docs](https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/local-inference#using-the-ersilia-cli) for more information on using the CLI.
