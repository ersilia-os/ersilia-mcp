"""An MCP server for the Ersilia model hub, built on the official FastMCP SDK.

Creates the FastMCP instance, registers the tool/resource modules, and serves
them over stdio so that MCP clients (e.g. Claude Desktop) can spawn it as a
subprocess.
"""

from fastmcp import FastMCP

from ersilia_mcp.tools import close, delete, fetch, predict, search, serve
from ersilia_mcp.tools.isaura import isaura_reader
from ersilia_mcp.utils.logging import logger

mcp = FastMCP("ersilia-mcp")
close.register(mcp)
delete.register(mcp)
fetch.register(mcp)
predict.register(mcp)
search.register(mcp)
serve.register(mcp)
isaura_reader.register(mcp)


def main() -> None:
    """Run the MCP server over stdio."""
    logger.success("Starting Ersilia MCP server over stdio")
    mcp.run()


if __name__ == "__main__":
    main()
