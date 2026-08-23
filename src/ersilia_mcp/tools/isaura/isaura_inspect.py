"""The ``check_cache`` tool for inspecting Isaura cache availability."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura cache-inspection tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def check_cache(
        model: str,
        input_data: str,
        version: str = "v1",
        bucket: str = "isaura-public",
    ) -> dict:
        """Check which inputs are already cached in Isaura without retrieving them.

        This is the inspection-only counterpart to ``get_precalculations``: it
        reports how many of the requested inputs are available in the Isaura
        store, but does not fetch or write any results. Use it to gauge cache
        coverage before deciding whether to read or recompute.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            Either a path to a CSV with an ``input``/``smiles`` column, or a
            string of one or more inputs separated by commas.
        version : str, optional
            Model version to inspect, by default ``"v1"``.
        bucket : str, optional
            Project bucket to inspect, by default ``"isaura-public"``.

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - num_requested: The number of inputs looked up
                - num_cached: How many are already cached
                - num_missing: How many are not cached
                - cached: Up to 20 of the inputs that are cached
                - missing: Up to 20 of the inputs that are not cached
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
        )
