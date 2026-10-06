"""The ``read_precalculations_from_isaura`` tool for retrieving Isaura results."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura read tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def read_precalculations_from_isaura(
        model: str,
        input_data: str,
        version: str = "v1",
        bucket: str = "isaura-public",
        output_path: str | None = None,
        verbose: bool = False,
    ) -> dict:
        """Retrieve cached results from Isaura instead of recomputing.

        Only the cached subset is returned; uncached inputs are counted rather
        than failing the read.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            A CSV path (``input``/``smiles`` column), or inputs separated by
            commas or newlines.
        version : str, optional
            Model version, by default ``"v1"``.
        bucket : str, optional
            Project bucket, by default ``"isaura-public"``.
        output_path : str, optional
            Where to write the cached values (CSV filepath); a temporary file is used if omitted.
        verbose : bool, optional
            Also return the list of uncached inputs.

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - num_requested: Total number of inputs
                - num_cached: How many were already cached
                - num_missing: How many were not cached
                - output_path: Where the cached results were written to (CSV filepath)
                  (``None`` when none of the inputs were cached in isaura)
                - columns: The result columns
            When ``verbose`` is ``True``, also includes:
                - cached: every cached input
                - missing: inputs not in the cache
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
            verbose,
        )
