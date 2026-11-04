"""MCP tool for serving Ersilia models."""

from fastmcp import Context, FastMCP

from ersilia_mcp.utils.model_operations import serve_model_helper
from ersilia_mcp.utils.progress import run_with_progress


def register(mcp: FastMCP) -> None:
    """Register the model tools on the MCP server."""

    @mcp.tool(timeout=900.0)
    async def serve_model(model: str, ctx: Context) -> dict:
        """Serve a model from the Ersilia model hub.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos8v1a``).

        Returns
        -------
        dict
            ``status`` is ``"ok"`` with ``model`` and ``info`` (from
            ``Model.info()``), or ``"error"`` with an ``error`` message.
        """
        return await run_with_progress(
            ctx, serve_model_helper, model, label=f"Serving {model}"
        )
