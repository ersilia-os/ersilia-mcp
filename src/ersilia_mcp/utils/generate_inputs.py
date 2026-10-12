"""Generate example inputs for served Ersilia models."""

import os
import tempfile
import traceback

from ersilia.api import Model

from ersilia_mcp.utils.logging import log_conda_environment, logger

PREVIEW_LIMIT = 20


def generate_inputs_helper(
    model_id: str,
    n_samples: int = 5,
    mode: str = "random",
    output_path: str | None = None,
) -> dict:
    """
    Generate example inputs for a served model and write them to a file.

    Wraps ersilia's ``example`` API, which samples inputs from the model that is
    currently served in the session. The model must already be served (see the
    ``serve_model`` tool) before calling this.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    n_samples : int, default=5
        Number of example inputs to generate.
    mode : str, default="random"
        Sampling strategy. One of ``"random"``, ``"deterministic"`` (the same
        inputs on every call), or ``"predefined"`` (drawn from the model's own
        example file, if any).
    output_path : str, optional
        Where to write the generated inputs (one per line). If omitted, a
        temporary file is created.

    Returns
    -------
    dict
        A summary containing the ``output_path``, the total ``num_samples``,
        and a ``samples`` preview capped at 20 entries, or an empty dict if
        generation failed.
    """
    try:
        log_conda_environment()
        logger.info(f"Generating {n_samples} '{mode}' sample(s) for model {model_id}")
        mdl = Model(model_id=model_id, verbose=True)
        samples = mdl.example(n_samples=n_samples, mode=mode)
        if not samples:
            logger.error(f"No samples generated for {model_id}; is the model served?")
            return {}

        if output_path is None:
            fd, output_path = tempfile.mkstemp(prefix=f"{model_id}_", suffix=".txt")
            os.close(fd)
        with open(output_path, "w") as f:
            f.write("\n".join(samples) + "\n")

        logger.success(f"Wrote {len(samples)} sample(s) to {output_path}")
        return {
            "output_path": output_path,
            "num_samples": len(samples),
            "samples": samples[:PREVIEW_LIMIT],
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error generating samples for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {}
