"""MCP tool for serving Ersilia models."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.model_operations import serve_model_helper


def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def serve_model(model: str) -> dict:
        """Serve a model from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            ``status`` is ``"ok"`` with ``model`` and ``info`` (from
            ``Model.info()``), or ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, serve_model_helper, model)
