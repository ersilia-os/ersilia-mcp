# Setting Up the Ersilia MCP Server with Claude Code

The MCP server lets Claude access the Ersilia model tools (search, fetch, serve, and predict). This guide walks you through setting it up. Once registered, Claude automatically starts the Ersilia MCP server as background subprocesses whenever you begin a new session.

## Step 1: Install Claude Code

* **CLI** (command line): [Installation guide](https://code.claude.com/docs/en/quickstart#step-1-install-claude-code)
* **VS Code extension** (optional, recommended if you use VS Code): [Install from marketplace](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)

## Step 2: Automatic Setup (Easiest)

This repository includes a configuration file (`.mcp.json`) that automatically connects Claude to the Ersilia server. Here's what happens behind the scenes:

1. When you open this project in Claude Code, it automatically loads the configuration.
2. Claude uses the `ersilia-mcp` conda environment you created during installation.
3. The server starts automatically whenever you begin a new Claude Code session.

To confirm that everything is connected, run:

```bash
claude mcp list
```

You should see: `ersilia-mcp: ... - ✔ Connected`.

**In VS Code?** You can also type `/mcp` in the Claude chat to see the list of connected MCP servers.

### Troubleshooting Automatic Setup

If you've used the Ersilia MCP server before and registered it manually, you may need to remove the old registration:

```bash
claude mcp remove ersilia-mcp
```

This ensures Claude uses the automatic configuration file instead of the old one.

## Step 3: Manual Setup (Alternative)

If automatic setup doesn't work, or you need a different environment name, register the MCP server manually using the `claude` CLI:

```bash
claude mcp add ersilia-mcp -- conda run --no-capture-output -n ersilia-mcp ersilia-mcp
```

Then verify that it's connected:

```bash
claude mcp list
```

## Troubleshooting

### Hanging Background Processes

Claude starts the MCP server as background subprocesses during new sessions, but occasionally these subprocesses stick around after the session is closed.

Find a hanging process with `ps aux | grep ersilia-mcp`. You should see something like this:

```text
(base) lehcar@lehcars-MacBook-Pro ersilia-mcp % ps aux | grep ersilia-mcp
lehcar           29118   0.0  0.0 410862736   6128   ??  S    Tue03PM   0:01.06 /Users/lehcar/miniconda3/envs/ersilia-mcp/bin/python3.12 /Users/lehcar/miniconda3/envs/ersilia-mcp/bin/ersilia-mcp
lehcar           28988   0.0  0.0 411058288   5760   ??  S    Tue03PM   0:00.39 /Users/lehcar/miniconda3/bin/python /Users/lehcar/miniconda3/bin/conda run --no-capture-output -n ersilia-mcp ersilia-mcp
lehcar           34781   0.0  0.0 435299520   1104 s001  R+   12:29AM   0:00.00 grep ersilia-mcp
```

The second column is the process ID. In this case, run `kill 29118` or `kill 28988` to stop the MCP server.

### Other Troubleshooting Resources

* [DEVELOPMENT.md](../../DEVELOPMENT.md) for more information on running and developing the server.
* [The official Claude Code docs](https://code.claude.com/docs/en/vs-code#option-3-add-a-local-stdio-server) for more information on local stdio servers.
