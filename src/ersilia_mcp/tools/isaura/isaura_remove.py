"""The ``remove_from_isaura`` tool for deleting specific inputs from a bucket."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.isaura import isaura_operations


def register(mcp: FastMCP) -> None:
    """Register the Isaura remove tool on the MCP server."""

    @mcp.tool(timeout=300.0)
    async def remove_from_isaura(
        model: str,
        input_data: str,
        bucket: str,
        version: str = "v1",
    ) -> dict:
        """Permanently remove specific inputs from a model's stored data in a bucket.

        Destructive. To delete a whole model/version or project bucket, use the
        CLI: ``isaura destroy -pn <bucket> [-m <model> -v <version>]``.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            A CSV path (``input``/``smiles`` column), or inputs separated by
            commas or newlines.
        bucket : str
            Project bucket to remove from.
        version : str, optional
            Model version, by default ``"v1"``.

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - num_requested: Total number of inputs
                - num_removed: Rows removed
                - num_not_found: Inputs that were not in the store
            On failure, ``status`` is ``"error"`` with an ``error`` message.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, isaura_operations.remove, model, input_data, bucket, version
        )
