"""MCP tools for running predictions against served Ersilia models"""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.predict import predict_helper


def register(mcp: FastMCP) -> None:
    """Register the predict tool on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def predict(model: str, input_data: str, output_path: str = None) -> dict:
        """Run predictions against a served model from the Ersilia model hub.

        The model must already be served (see the ``serve_model`` tool).

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            Either a path to a file (one input per line) or a string of one or
            more inputs separated by newlines or commas.
        output_path : str, optional
            Where to write the results CSV. If omitted, a temporary file is
            created.

        Returns
        -------
        dict
            A summary containing:
                - output_path: The CSV file the predictions were written to
                - num_predictions: The number of predictions produced
                - columns: The result columns
            or an empty dict if prediction failed.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, predict_helper, model, input_data, output_path
        )
