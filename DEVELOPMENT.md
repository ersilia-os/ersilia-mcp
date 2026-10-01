## Setup

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
poetry config virtualenvs.create false --local
poetry env use $(which python)
# for local development
poetry install --all-extras
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

## Isaura precalculation store

TODO: Remove CLI commands as we add new mcp tools

Two tools read from the [Isaura](https://github.com/ersilia-os/isaura) store (a
MinIO instance managed by Isaura over Docker). Docker must be running.

| Tool                               | Purpose                                                         |
| ---------------------------------- | --------------------------------------------------------------- |
| `inspect_isaura_cache`             | Counts which inputs are cached, without retrieving anything.    |
| `read_precalculations_from_isaura` | Retrieves the cached subset and writes it to a CSV.             |

Both take `model`, `input_data` (a CSV path or a comma-separated string),
`version`, and `bucket`, and both accept `verbose` to list the inputs that are
missing from the cache instead of only counting them. `inspect_isaura_cache`
additionally lists the cached inputs when verbose;
`read_precalculations_from_isaura` also takes an `output_path` for the
retrieved results, and reports `columns` plus the `output_path` it wrote.

Uncached inputs are skipped rather than failing the read, so a partial hit
returns the cached rows and a `num_missing` count.

Start the local store — this creates the reserved `isaura-public` and
`isaura-private` buckets:
```bash
isaura engine --start        # start local MinIO
isaura engine                # show Docker + MinIO status
isaura configure --test-credentials   # verify local (and cloud) connectivity
```

The store is empty on first start. Populate it by writing model outputs (the
CSV must have an `input` or `smiles` column — e.g. the output of the `predict`
tool):
```bash
isaura write -i data/eos3b5e_output.csv -m eos3b5e -v v1 -pn isaura-public
```

Stop the store when you're done:
```bash
isaura engine --stop
```

> After editing tool code, reinstall (`pip install -e .`) and reconnect the MCP
> server (`/mcp reconnect` in the client) so the running subprocess picks up
> the changes — otherwise it keeps serving the previously imported code.

## Linting and Code Quality

Run ruff to check and format code:
```bash
poetry run ruff check .
poetry run ruff format .
```

## Tests

The test suite is split into two categories:

**Unit tests** (fast, safe, run offline):
```bash
poetry run pytest -v -m "not integration"
```

These test the MCP tools and utilities with mocked Ersilia API calls. Safe to run locally without side effects.

**Integration tests** (slower, hit real APIs, mark with `@pytest.mark.integration`):
```bash
poetry run pytest -v -m integration
```

These call the live Ersilia Model Hub APIs to validate the full model lifecycle (fetch, check, serve, generate_inputs, predict, cache, inspect, read, close, delete) against real data. Note: fetching models can populate `~/eos/repository/`, so clean up afterwards if needed.

The cache/inspect/read steps need a running Isaura store, so start it first (see [Isaura precalculation store](#isaura-precalculation-store)):
```bash
isaura engine --start
poetry run pytest -v -m integration
isaura engine --stop
```

The lifecycle test writes its predictions into the `isaura-public` bucket, so the store accumulates rows across runs.

## CI/CD

A [GitHub Action](.github/workflows/ci.yml) runs on every push to `main` and on pull requests.

## Debugging Ersilia operations
Locally fetched/served models are stored in the `~/eos/` directory.

To manually check which models are fetched, check `~/eos/repository/`.
To manually check which models are served, check `~/eos/sessions/`.

Note: Since we're using the ersilia python package, the ersilia CLI should also be installed in your conda environment. See [these docs](https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/local-inference#using-the-ersilia-cli) for more information on using the CLI.
