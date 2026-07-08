"""Wrappers for Ersilia model operations."""

import traceback

from ersilia.api import Model

from ersilia_mcp.utils.logging import logger, log_conda_environment


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
        log_conda_environment()
        logger.info(f"Checking if model {model_id} is fetched")
        mdl = Model(model_id=model_id)
        is_already_fetched = mdl.is_fetched()
        logger.info(f"Model {model_id} already fetched: {is_already_fetched}")
        if not is_already_fetched:
            logger.info(f"Fetching model {model_id}")
            mdl.fetch()
            logger.info(f"Fetch completed for {model_id}")
        return mdl.is_fetched()
    except (Exception, SystemExit) as e:
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
        log_conda_environment()
        mdl = Model(model_id=model_id)
        return mdl.is_fetched()
    except (Exception, SystemExit) as e:
        logger.error(
            f"Encountered an error while checking if {model_id} is fetched: {str(e)}"
        )
        logger.error(traceback.format_exc())
        return False


def serve_model_helper(model_id: str) -> dict:
    """
    Serve a fetched model

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        A dictionary containing information from Model.info()
        or an empty dict if serving failed.
    """
    try:
        logger.info(f"Serving model {model_id}...")
        mdl = Model(model_id=model_id, verbose=True)
        mdl.serve()
        logger.info("Successfully served the model. You can run `docker ps` to manually confirm the model is served.")
        logger.info(f"Model information: {mdl.info()}")
        return mdl.info()
    except RuntimeError as e:
        logger.error(f"Encountered an error while serving {model_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {}
    
def close_model_helper(model_id: str) -> bool:
    """
    Close the current session and clean up associated resources.

    Terminates the model server and removes the session file, freeing up system resources.

    Returns
    -------
    bool
        True if the session was successfully closed, False otherwise.
    """
    try:
        logger.info(f"Closing model {model_id}...")
        mdl = Model(model_id=model_id, verbose=True)
        mdl.close()
        return True
    except (Exception, SystemExit) as e:
        logger.error(
            f"Encountered an error closing model {model_id}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        return False
