"""The ``inspect_isaura_cache`` tool for inspecting Isaura cache availability."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura cache-inspection tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def inspect_isaura_cache(
        model: str,
        input_data: str,
        version: str = "v1",
        bucket: str = "isaura-public",
        verbose: bool = False,
    ) -> dict:
        """Check which inputs Isaura has cached, without retrieving them.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            A CSV path (``input``/``smiles`` column), or inputs separated by
            commas.
        version : str, optional
            Model version, by default ``"v1"``.
        bucket : str, optional
            Project bucket, by default ``"isaura-public"``.
        verbose : bool, optional
            When true, return the full list of cached and missing inputs (not just counts).

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - num_requested: The number of inputs looked up
                - num_cached: How many are already cached
                - num_missing: How many are not cached
            When ``verbose`` is ``True``, also includes:
                - cached: The inputs that are cached
                - missing: The inputs that are not cached
            On failure (e.g. the local store is unreachable), ``status`` is
            ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            isaura_operations.inspect,
            model,
            input_data,
            version,
            bucket,
            verbose,
        )
