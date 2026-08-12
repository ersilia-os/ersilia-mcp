"""The ``read_precalculations`` tool for retrieving results from Isaura."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura read tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def read_precalculations(
        model: str,
        input_data: str,
        version: str = "v1",
        bucket: str = "isaura-public",
        output_path: str | None = None,
    ) -> dict:
        """Check which inputs are cached in Isaura and retrieve those results.

        Looks up inputs in an Isaura store instead of recomputing them, which
        is much faster when results are already cached. Inputs are first
        inspected for availability; only the cached subset is retrieved, and
        any missing inputs are reported rather than failing the whole read.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            Either a path to a file (one input per line) or a string of one or
            more inputs separated by newlines or commas.
        version : str, optional
            Model version to read, by default ``"v1"``.
        bucket : str, optional
            Project bucket to read from, by default ``"isaura-public"``.
        output_path : str, optional
            Where to write the retrieved results CSV. Only written when at
            least one input is cached; if omitted, a temporary file is created.

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - num_requested: The number of inputs looked up
                - num_cached: How many were already cached
                - num_missing: How many were not cached
                - missing: Up to 20 of the inputs that were not cached
                - output_path: The CSV the cached results were written to
                  (``None`` when nothing was cached)
                - columns: The result columns
            On failure (e.g. the local store is unreachable), ``status`` is
            ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            isaura_operations.read,
            model,
            input_data,
            version,
            bucket,
            output_path,
        )
