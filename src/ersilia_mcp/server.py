"""An MCP server for the Ersilia model hub, built on the official FastMCP SDK.

Creates the FastMCP instance, registers the tool/resource modules, and serves
them over stdio so that MCP clients (e.g. Claude Desktop) can spawn it as a
subprocess.
"""

from ersilia_mcp.utils.logging import logger

from mcp.server.fastmcp import FastMCP

from ersilia_mcp.tools import fetch, search

mcp = FastMCP("ersilia-mcp")
search.register(mcp)
fetch.register(mcp)


def main() -> None:
    """Run the MCP server over stdio."""
    logger.success("Starting Ersilia MCP server over stdio")
    mcp.run()


if __name__ == "__main__":
    main()
