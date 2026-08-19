"""MCP tool for generating example inputs for served Ersilia models."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.generate_inputs import generate_inputs_helper


def register(mcp: FastMCP) -> None:
    """Register the generate_inputs tool on the MCP server."""

    @mcp.tool(timeout=120.0)
    async def generate_inputs(
        model: str, n_samples: int = 5, mode: str = "random"
    ) -> list[str]:
        """Generate example inputs for a served model from the Ersilia model hub.

        The model must already be served (see the ``serve_model`` tool). The
        generated inputs can be fed directly into the ``predict`` tool.

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        n_samples : int, optional
            Number of example inputs to generate (default 5).
        mode : str, optional
            Sampling strategy: ``"random"`` (default), ``"deterministic"`` (the
            same inputs on every call), or ``"predefined"`` (drawn from the
            model's own example file, if any).

        Returns
        -------
        list[str]
            The generated example inputs, or an empty list if generation failed.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, generate_inputs_helper, model, n_samples, mode
        )
