"""MCP tool for generating example inputs for served Ersilia models."""

import asyncio

from fastmcp import FastMCP

from ersilia_mcp.utils.generate_inputs import generate_inputs_helper


def register(mcp: FastMCP) -> None:
    """Register the generate_inputs tool on the MCP server."""

    @mcp.tool(timeout=120.0)
    async def generate_inputs(
        model: str,
        n_samples: int = 5,
        mode: str = "random",
        output_path: str | None = None,
    ) -> dict:
        """Generate example inputs for a served model from the Ersilia model hub.

        The model must already be served (see ``serve_model``).

        Parameters
        ----------
        model : str
            Model identifier (e.g., ``eos3b5e``).
        n_samples : int, optional
            Number of example inputs to generate (default 5).
        mode : str, optional
            ``"random"`` (default), ``"deterministic"`` (same inputs every
            call), or ``"predefined"`` (from the model's example file, if any).
        output_path : str, optional
            Where to write the generated inputs. A temp file is used if omitted.

        Returns
        -------
        dict
            A summary containing:
                - output_path: The file the generated inputs were written to
                - num_samples: The total number of samples generated
                - samples: A preview of up to 20 samples; see output_path for
                  the rest
            or an empty dict if generation failed.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, generate_inputs_helper, model, n_samples, mode, output_path
        )
