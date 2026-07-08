"""MCP tools for serving Ersilia models and closing Ersilia models"""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import serve_model_helper

def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def serve_model(model: str) -> bool:
        """Serve a model from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            A dictionary containing:
                - url: The URL where the model is being served
                - session: The session object
                - server: The server object
            or an empty dict if serving failed.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, serve_model_helper, model)
