"""MCP tools for closing served Ersilia models."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import close_model_helper


def register(mcp: FastMCP) -> None:
    """Register the close model tool on the MCP server."""

    @mcp.tool(timeout=10.0)
    async def close_model(model: str) -> bool:
        """Close a served model. Terminates the model server and cleans up associated resources.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        bool
            True if closed successfully, False otherwise.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, close_model_helper, model)
