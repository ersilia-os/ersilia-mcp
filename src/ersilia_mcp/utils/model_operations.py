"""Wrappers for Ersilia model operations."""

import traceback

from ersilia.api import Model

from ersilia_mcp.utils.errors import error_result
from ersilia_mcp.utils.logging import log_conda_environment, logger


def fetch_model_helper(model_id: str) -> dict:
    """
    Fetch a model from the Ersilia model hub.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        ``{"status": "ok", "model": str, "fetched": True}`` on success, or
        ``{"status": "error", "error": str}`` if the fetch failed.
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
        if not mdl.is_fetched():
            return error_result(
                f"Fetch of {model_id} finished but the model is not marked as fetched"
            )
        return {"status": "ok", "model": model_id, "fetched": True}
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error fetching model {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return error_result(e)


def check_model_fetched_helper(model_id: str) -> dict:
    """
    Check if a model is fetched from the Ersilia model hub.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        ``{"status": "ok", "model": str, "fetched": bool}``, or
        ``{"status": "error", "error": str}`` if the check itself failed (which
        is distinct from the model simply not being fetched).
    """
    try:
        log_conda_environment()
        mdl = Model(model_id=model_id)
        return {"status": "ok", "model": model_id, "fetched": bool(mdl.is_fetched())}
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(
            f"Encountered an error while checking if {model_id} is fetched: {e!s}"
        )
        logger.error(traceback.format_exc())
        return error_result(e)


def serve_model_helper(model_id: str) -> dict:
    """
    Serve a fetched model.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        ``{"status": "ok", "model": str, "info": dict}`` where ``info`` is the
        output of ``Model.info()``, or ``{"status": "error", "error": str}`` if
        serving failed.
    """
    try:
        log_conda_environment()
        logger.info(f"Serving model {model_id}...")
        mdl = Model(model_id=model_id, verbose=True)
        mdl.serve()
        info = mdl.info()
        logger.info(
            "Successfully served the model. You can run `docker ps` to manually confirm the model is served."
        )
        logger.info(f"Model information: {info}")
        return {"status": "ok", "model": model_id, "info": info}
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error while serving {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return error_result(e)


def close_model_helper(model_id: str) -> dict:
    """
    Close a served model and clean up associated resources.

    Terminates the model server and removes the session file, freeing up system resources.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        ``{"status": "ok", "model": str}`` on success, or
        ``{"status": "error", "error": str}`` if closing failed.
    """
    try:
        logger.info(f"Closing model {model_id}...")
        mdl = Model(model_id=model_id, verbose=True)
        mdl.close()
        return {"status": "ok", "model": model_id}
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error closing model {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return error_result(e)


def delete_model_helper(model_id: str) -> dict:
    """
    Delete a model from the Ersilia model hub.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos8v1a``).

    Returns
    -------
    dict
        ``{"status": "ok", "model": str}`` on success, or
        ``{"status": "error", "error": str}`` if deletion failed.
    """
    try:
        logger.info(f"Deleting model {model_id}...")
        mdl = Model(model_id=model_id)
        mdl.delete()
        logger.info(f"Successfully deleted model {model_id}")
        return {"status": "ok", "model": model_id}
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error deleting model {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return error_result(e)
