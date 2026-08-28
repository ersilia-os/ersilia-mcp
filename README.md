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
| Tool      | `generate_inputs`     | Samples example inputs from a served model.                 |
| Tool      | `predict`             | Runs predictions with a served model and writes a CSV.      |
| Tool      | `close_model`         | Stops a served model and frees its resources.               |
| Tool      | `delete_model`        | Deletes a fetched model from local storage.                 |

A typical workflow is `search_model` → `fetch_model` → `serve_model` → `predict`
→ `close_model`. You can optionally call `generate_inputs` after serving to
sample example inputs to feed into `predict`, and `delete_model` to remove the
model from local storage.

## Installation

Ensure you have the following installed:
* [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation) (miniconda is fine)
* [Docker](https://docs.docker.com/get-docker/)
* [git](https://git-scm.com/install/source)

Clone the repository locally using git:
```bash
git clone git@github.com:ersilia-os/ersilia-mcp.git
```

Create a new virtual conda environment, activate it, and install the necessary packages:
```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
pip install .
```

## Client Setup & Registration

This MCP server has been tested mainly on Claude (specifically using Claude Code), but it supports any Model Context Protocol (MCP) host or model provider (such as Gemini or ChatGPT) that supports local stdio MCP servers.

**Note on Claude Code:** This repository is set up to be automatically configured with Claude Code out of the box. It includes a project-scoped `.mcp.json` configuration file so that when you run Claude Code in this workspace, the Ersilia MCP server is registered and started automatically.

Currently, we only have dedicated setup and registration documentation for:
- [Claude Code Setup Guide](docs/mcp_setup/claude_code.md)
- [Gemini Setup Guide](docs/mcp_setup/gemini.md)

We would love to receive documentation updates and setup guides for other MCP clients and platforms. If you have successfully set up this server with another client, please consider adding a new setup guide to `docs/mcp_setup/`! See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

For further details on manual registration, debugging, or full development setup, please see [DEVELOPMENT.md](DEVELOPMENT.md).

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit
organization fueling sustainable research in the Global South. Ersilia's main
asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an
open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
