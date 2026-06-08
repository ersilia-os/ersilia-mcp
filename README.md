# MCP server for the Ersilia Model Hub

A [Model Context Protocol](https://modelcontextprotocol.io) server built on the
official FastMCP SDK. It lets MCP clients search the Ersilia Model Hub catalog,
served over stdio.

| Primitive | Name               | Description                                   |
| --------- | ------------------ | --------------------------------------------- |
| Tool      | `search_model`     | Searches the Ersilia model hub catalog.       |

## Local Installation

This server shells out to the [Ersilia CLI](https://github.com/ersilia-os/ersilia),
which lives in its **own** conda environment. Install the two separately.

```bash
conda create -n ersilia-mcp python=3.12
conda activate ersilia-mcp
pip install .
```

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

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit
organization fueling sustainable research in the Global South. Ersilia's main
asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an
open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
