"""The ``write_precalculations_to_isaura`` tool for storing results in Isaura."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura write tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def write_precalculations_to_isaura(
        model: str,
        input_csv: str,
        version: str = "v1",
        bucket: str = "isaura-public",
    ) -> dict:
        """Write predictions to Isaura, keyed by input. Counterpart to ``read_precalculations_from_isaura``.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_csv : str
            Path to a results CSV with an ``input``/``smiles`` column plus
            output columns, e.g. what ``predict`` writes.
        version : str, optional
            Model version to write under, by default ``"v1"``.
        bucket : str, optional
            Project bucket to write to, by default ``"isaura-public"``.

        Returns
        -------
        dict
            ``status`` ``"ok"`` with ``num_rows`` and ``columns``, or
            ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            isaura_operations.write,
            model,
            input_csv,
            version,
            bucket,
        )
