"""MCP tools for running predictions against served Ersilia models"""

from fastmcp import Context, FastMCP

from ersilia_mcp.utils.predict import predict_helper
from ersilia_mcp.utils.progress import run_with_progress


def register(mcp: FastMCP) -> None:
    """Register the predict tool on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def predict(
        model: str,
        input_data: str,
        ctx: Context,
        output_path: str | None = None,
    ) -> dict:
        """Run predictions against a served model from the Ersilia model hub.

        The model must already be served (see ``serve_model``).

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        input_data : str
            A filepath (one input per line), or inputs separated by commas or
            newlines.
        output_path : str, optional
            Where to write the results CSV. A temp file is used if omitted.

        Returns
        -------
        dict
            On success, ``status`` is ``"ok"`` with:
                - output_path: The CSV file the predictions were written to
                - num_predictions: The number of predictions produced
                - columns: The result columns
            On failure, ``status`` is ``"error"`` with an ``error`` message.
        """
        return await run_with_progress(
            ctx,
            predict_helper,
            model,
            input_data,
            output_path,
            label=f"Predicting with {model}",
        )
