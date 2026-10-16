"""The ``persist_isaura_data`` tool for routing project data into shared buckets."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura persist tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def persist_isaura_data(
        model: str,
        bucket: str,
        version: str = "v1",
    ) -> dict:
        """Persist a project bucket's results into ``isaura-public``/``isaura-private``.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        bucket : str
            Project bucket whose rows are routed to the shared buckets.
        version : str, optional
            Model version, by default ``"v1"``.

        Returns
        -------
        dict
            ``status`` is ``"ok"`` with ``model``, ``version`` and ``bucket``,
            or ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, isaura_operations.persist, model, bucket, version
        )
