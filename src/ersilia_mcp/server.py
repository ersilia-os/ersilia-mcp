"""A minimal "hello world" MCP server built on the official FastMCP SDK.

Exposes a single ``hello`` tool and a static greeting resource, served over
stdio so that MCP clients (e.g. Claude Desktop) can spawn it as a subprocess.
"""

from mcp.server.fastmcp import FastMCP

from ersilia_mcp.utils.logging import logger

mcp = FastMCP("ersilia-mcp")


@mcp.tool()
def hello(name: str) -> str:
    """Return a friendly greeting.

    Parameters
    ----------
    name : str
        The name to greet.

    Returns
    -------
    str
        The greeting ``"Hello, {name}!"``.
    """
    logger.info("Greeting %s", name)
    return f"Hello, {name}!"


@mcp.resource("greeting://hello")
def greeting() -> str:
    """Provide a static greeting message as an MCP resource."""
    return "Hello from the Ersilia MCP server!"


def main() -> None:
    """Run the MCP server over stdio."""
    logger.success("Starting Ersilia MCP server over stdio")
    mcp.run()


if __name__ == "__main__":
    main()
