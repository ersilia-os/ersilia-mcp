# Hello-world MCP server for Ersilia

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server built
on the official FastMCP SDK. It exposes one tool and one resource, served over
stdio, as a starting point for Ersilia MCP integrations.

| Primitive | Name              | Description                          |
| --------- | ----------------- | ------------------------------------ |
| Tool      | `hello`           | Returns `"Hello, {name}!"`.          |
| Resource  | `greeting://hello`| A static greeting message.           |

## Installation

```bash
conda create -n ersilia_mcp python=3.12
conda activate ersilia_mcp
pip install git+https://github.com/ersilia-os/ersilia-mcp.git
```

## Running

The server speaks stdio, so MCP clients spawn it as a subprocess. Run it
directly to check it starts:

```bash
ersilia-mcp
```

## Register
### Claude Code

`claude mcp add` needs the absolute path to the entry point, and it does not
inherit your activated conda environment. Ask conda for the path, then register
it:
```bash
conda activate ersilia_mcp
which ersilia-mcp   # e.g. /Users/you/miniconda3/envs/ersilia_mcp/bin/ersilia-mcp

claude mcp add ersilia-mcp "$(which ersilia-mcp)"
```

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit
organization fueling sustainable research in the Global South. Ersilia's main
asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an
open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
