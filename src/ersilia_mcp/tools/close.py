"""MCP tools for closing served Ersilia models."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import close_model_helper


def register(mcp: FastMCP) -> None:
    """Register the close model tool on the MCP server."""

    @mcp.tool(timeout=10.0)
    async def close_model(model: str) -> dict:
        """Close a served model, freeing its resources.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            ``status`` is ``"ok"`` if closed, or ``"error"`` with an ``error``
            message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, close_model_helper, model)
