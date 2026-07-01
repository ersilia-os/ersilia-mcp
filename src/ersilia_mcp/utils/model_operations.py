"""Wrappers for Ersilia model operations."""

import os
import sys
import traceback

from ersilia.api import Model

from ersilia_mcp.utils.logging import logger


def _log_conda_environment() -> None:
    """Log the active conda environment and Python interpreter for debugging."""
    logger.debug(f"CONDA_DEFAULT_ENV={os.environ.get('CONDA_DEFAULT_ENV')}")
    logger.debug(f"CONDA_PREFIX={os.environ.get('CONDA_PREFIX')}")
    logger.debug(f"sys.executable={sys.executable}")
    logger.debug(f"sys.prefix={sys.prefix}")


def fetch_model_helper(model_id: str) -> bool:
    """
    Fetch a model from the Ersilia model hub.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    bool
        True if the model was successfully fetched.
    """
    try:
        _log_conda_environment()
        logger.info(f"Checking if model {model_id} is fetched")
        mdl = Model(model_id=model_id)
        is_already_fetched = mdl.is_fetched()
        logger.info(f"Model {model_id} already fetched: {is_already_fetched}")
        if not is_already_fetched:
            logger.info(f"Fetching model {model_id}")
            mdl.fetch()
            logger.info(f"Fetch completed for {model_id}")
        return mdl.is_fetched()
    except Exception as e:
        logger.error(f"Error fetching model {model_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def check_model_fetched_helper(model_id: str) -> bool:
    """
    Check if a model is fetched from the Ersilia model hub.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    bool
        True if model is already fetched. False otherwise
    """
    try:
        _log_conda_environment()
        mdl = Model(model_id=model_id)
        return mdl.is_fetched()
    except Exception as e:
        logger.error(
            f"Encountered an error while checking if {model_id} is fetched: {str(e)}"
        )
        logger.error(traceback.format_exc())
        return False
