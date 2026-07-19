# MCP server for the Ersilia Model Hub

A [Model Context Protocol](https://modelcontextprotocol.io) server built on the
official FastMCP SDK. It lets MCP clients search the Ersilia Model Hub catalog
and fetch, serve, and run its AI/ML models, all over stdio.

| Primitive | Name                  | Description                                                  |
| --------- | --------------------- | ----------------------------------------------------------- |
| Tool      | `search_model`        | Searches the Ersilia model hub catalog by keyword.          |
| Tool      | `fetch_model`         | Downloads a model to the local machine.                     |
| Tool      | `check_model_fetched` | Reports whether a model has already been fetched.           |
| Tool      | `serve_model`         | Starts a fetched model so it can accept predictions.        |
| Tool      | `predict`             | Runs predictions with a served model and writes a CSV.      |
| Tool      | `close_model`         | Stops a served model and frees its resources.               |

A typical workflow is `search_model` → `fetch_model` → `serve_model` → `predict`
→ `close_model`.

## Installation

Prerequisite: Ensure you have [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation) installed (miniconda is fine).

Create a new virtual conda environment, activate it, and install the necessary packages:
```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
pip install .
```

## Register with Claude Code

The repo ships a [`.mcp.json`](.mcp.json) that auto-registers the server. Just verify it's running:

```bash
claude mcp list
```

You should see `ersilia-mcp: ... - ✔ Connected`.

See [DEVELOPMENT.md](DEVELOPMENT.md) for manual registration, debugging, or development setup.

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit
organization fueling sustainable research in the Global South. Ersilia's main
asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an
open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
