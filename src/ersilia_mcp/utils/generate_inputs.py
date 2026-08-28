"""Generate example inputs for served Ersilia models."""

import traceback

from ersilia.api import Model

from ersilia_mcp.utils.logging import log_conda_environment, logger


def generate_inputs_helper(
    model_id: str, n_samples: int = 5, mode: str = "random"
) -> list[str]:
    """
    Generate example inputs for a served model.

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

    Returns
    -------
    list[str]
        The generated example inputs, or an empty list if generation failed.
    """
    try:
        log_conda_environment()
        logger.info(f"Generating {n_samples} '{mode}' sample(s) for model {model_id}")
        mdl = Model(model_id=model_id, verbose=True)
        samples = mdl.example(n_samples=n_samples, mode=mode)
        if not samples:
            logger.error(f"No samples generated for {model_id}; is the model served?")
            return []
        logger.success(f"Generated {len(samples)} sample(s) for {model_id}")
        return samples
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error generating samples for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return []
