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

## MCP Client Setup & Registration

This MCP server has been tested mainly on Claude (specifically using Claude Code), but it can be used with any model provider or host (Gemini, ChatGPT, Claude) that supports local stdio MCP servers.

**Note on Claude Code:** This repository is set up to be automatically configured with Claude Code out of the box. It includes a project-scoped `.mcp.json` configuration file so that when you run Claude Code in this workspace, the Ersilia MCP server is registered and started automatically.

Currently, we only have dedicated setup and registration documentation for:
- [Claude Code Setup Guide](docs/mcp_setup/claude_code.md)
- [Gemini Setup Guide](docs/mcp_setup/gemini.md)
- [Ollama (Qwen3) Setup Guide](docs/mcp_setup/ollama.md)

We would love to receive documentation updates and setup guides for other MCP clients and platforms. If you have successfully integrated this server with other environments, please feel free to submit a pull request with new client guides! See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### Claude Code Registration Summary

For quick reference, the repository ships a project-scoped [`.mcp.json`](.mcp.json) that automatically configures Claude Code to launch the MCP server over stdio.

Verify the server is running:
```bash
claude mcp list
```

You should see `ersilia-mcp: ... - ✔ Connected`.

For a full step-by-step walkthrough of automatic vs. manual registration, caveats, and extension setups, refer to the [Claude Code Setup Guide](docs/mcp_setup/claude_code.md).

### Using the Ollama (Local LLM) Codespace

If you opened this repo in the `ersilia-mcp-local-llm` devcontainer config (`.devcontainer/ollama/`), Ollama and `ollmcp` are already installed and `qwen3:1.7b` is already pulled by the time the container finishes creating, and the Ollama daemon is started automatically on every attach.

The one step that's still manual: start `ollmcp` yourself from the repo root once the codespace is ready:
```bash
ollmcp --servers-json .mcp.json --model qwen3:1.7b
```

See the [Ollama (Qwen3) Setup Guide](docs/mcp_setup/ollama.md) for the full walkthrough, including upgrading to the larger `qwen3:4b` model.

### Authenticating Claude Code in the Claude Codespace

The default devcontainer (`.devcontainer/devcontainer.json`) installs Claude Code but doesn't configure authentication, so it prompts for an interactive OAuth login on first run — awkward in a fresh Codespace.

To skip that prompt, set `ANTHROPIC_API_KEY` as a [Codespaces secret](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-encrypted-secrets-for-your-codespace-or-codespaces) scoped to this repository (GitHub → Settings → Codespaces → "New secret", value from the [Anthropic Console](https://console.anthropic.com/)). Codespaces injects secrets as environment variables automatically, and Claude Code uses `ANTHROPIC_API_KEY` directly instead of prompting for OAuth whenever it's set. Never commit the key itself to the repo.

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

Five tools use the [Isaura](https://github.com/ersilia-os/isaura) store (a
MinIO instance managed by Isaura over Docker) which needs to be running. Docker must be running.

| Tool                               | Purpose                                                         |
| ---------------------------------- | --------------------------------------------------------------- |
| `inspect_isaura_cache`             | Counts which inputs are cached, without retrieving anything.    |
| `read_precalculations_from_isaura` | Retrieves the cached subset and writes it to a CSV.             |
| `write_precalculations_to_isaura`  | Stores a results CSV in the cache.                              |
| `persist_isaura_data`              | Routes rows from a project bucket into `isaura-public`/`isaura-private`. |
| `remove_from_isaura`               | Removes specific inputs from a model/version in a bucket.       |

`persist_isaura_data` takes `model`, a required `bucket` (the project bucket to
persist from) and `version`. `remove_from_isaura` takes `model`, `input_data`
(a CSV path or a comma/newline-separated string), a required `bucket` and
`version`, and reports `num_removed` and `num_not_found`. Removal is
destructive. To delete a whole model/version or project bucket, use the CLI:
`isaura destroy -pn myproject -m eos3b5e -v v1` (or `isaura destroy -pn myproject`).

Start the local store — this creates the reserved `isaura-public` and
`isaura-private` buckets:
```bash
isaura engine --start        # start local MinIO
isaura engine                # show Docker + MinIO status
isaura configure --test-credentials   # verify local (and cloud) connectivity
```

Stop the store when you're done:
```bash
isaura engine --stop
```
> [!NOTE]
> After editing tool code, restart and reconnect the MCP
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
> [!NOTE]
> It is not recommended to run these tests locally. See [CI/CD](#cicd) for info on the GitHub Action that runs these tests.

These call the live Ersilia Model Hub APIs to validate the full model lifecycle (fetch, check, serve, generate_inputs, predict, cache, inspect, read, remove, persist, close, delete) against real data. Fetching models can populate `~/eos/repository/`, so clean up afterwards if needed.

The cache/inspect/read steps need a running Isaura store, so start it first (see [Isaura precalculation store](#isaura-precalculation-store)):
```bash
isaura engine --start
poetry run pytest -v -m integration
isaura engine --stop
```

The lifecycle test writes its predictions into the `isaura-public` bucket, so the store accumulates rows across runs. Its remove/persist steps use a throwaway `mcp-it-*` project bucket (made with `isaura create -pn <name> --access private`) that is destroyed afterwards.

## CI/CD

A [GitHub Action](.github/workflows/ci.yml) runs on every push to `main` and on pull requests.

## Debugging Ersilia operations
Locally fetched/served models are stored in the `~/eos/` directory.

To manually check which models are fetched, check `~/eos/repository/`.
To manually check which models are served, check `~/eos/sessions/`.

Note: Since we're using the ersilia python package, the ersilia CLI should also be installed in your conda environment. See [these docs](https://ersilia.gitbook.io/ersilia-book/ersilia-model-hub/local-inference#using-the-ersilia-cli) for more information on using the CLI.
