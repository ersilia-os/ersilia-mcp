"""MCP tools for deleting Ersilia models"""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import delete_model_helper


def register(mcp: FastMCP) -> None:
    """Register the delete model tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def delete_model(model: str) -> bool:
        """Delete a fetched model from local storage.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        bool
            True if deleted, False otherwise.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, delete_model_helper, model)
