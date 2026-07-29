# Setting Up the Ersilia MCP Server with Gemini

The Model Context Protocol (MCP) server lets the Gemini CLI access the Ersilia model tools (search, fetch, serve, and predict). This guide walks you through setting up the MCP server.

> **Note:** The Gemini CLI is scheduled to be deprecated by the end of 2026. Migration to the next-generation Antigravity CLI is recommended. The Antigravity CLI is not currently documented here as it has not been tested with this setup, but you can refer to the official [Antigravity Getting Started Guide](https://antigravity.google/docs/getting-started).

## Step 1: Install Gemini CLI

Ensure you have the Gemini CLI installed by following the [Gemini CLI Installation Guide](https://geminicli.com/docs/get-started/installation/).

## Step 2: Auto-Registration

This repository includes a configuration file (`.mcp.json`) that can automatically configure Gemini. Copy `.mcp.json` to `.gemini/settings.json`:

```bash
mkdir -p .gemini && cp .mcp.json .gemini/settings.json
```

## Step 3: Manual Registration (Alternative)

If you prefer to add the MCP server manually using the command line:

```bash
gemini mcp add ersilia-mcp conda run --no-capture-output -n ersilia-mcp ersilia-mcp
```
This will create or update the `.gemini/settings.json` file in your project directory.

## Step 4: Verification

To verify that the MCP server is correctly registered and running:

```bash
gemini mcp list
```

You should see output similar to:
```text
Configured MCP servers:

✓ ersilia-mcp: /Users/lehcar/miniconda3/bin/conda run --no-capture-output -n ersilia-mcp ersilia-mcp (stdio) - Connected
```
