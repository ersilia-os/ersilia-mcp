"""MCP tools for fetching Ersilia models and seeing if the model is fetched"""

import asyncio

from fastmcp import Context, FastMCP

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    fetch_model_helper,
)
from ersilia_mcp.utils.progress import run_with_progress


def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def fetch_model(model: str, ctx: Context) -> dict:
        """Fetch a model from the Ersilia model hub. This can take a few minutes.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            ``status`` is ``"ok"`` with ``model`` and ``fetched`` (``True``), or
            ``"error"`` with an ``error`` message.
        """
        return await run_with_progress(
            ctx, fetch_model_helper, model, label=f"Fetching {model}"
        )

    @mcp.tool(timeout=10.0)
    async def check_model_fetched(model: str) -> dict:
        """Check if a model is fetched from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            ``status`` is ``"ok"`` with ``fetched`` (``True`` or ``False``), or
            ``"error"`` with an ``error`` message if the check itself failed.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, check_model_fetched_helper, model)
