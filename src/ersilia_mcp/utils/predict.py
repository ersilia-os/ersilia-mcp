"""Run predictions against served Ersilia models."""

import os
import re
import tempfile
import traceback
from collections.abc import Callable

from ersilia.api import Model

from ersilia_mcp.utils.errors import error_result
from ersilia_mcp.utils.logging import log_conda_environment, logger

# Inputs per ``Model.run`` call when predicting a large set. Ersilia batches at
# the same size internally, so this costs nothing in throughput and lets us
# report real progress between chunks.
CHUNK_SIZE = 1000


def parse_input(input_data: str) -> list:
    """
    Turn the tool input into a list of prediction inputs.

    If ``input_data`` points to an existing file, its non-empty lines are read.
    Otherwise the string is treated as a delimited list, split on newlines and
    commas. Inputs are passed through as-is; ersilia validates them at run time
    (unparseable inputs come back with empty predictions).

    Parameters
    ----------
    input_data : str
        Either a path to a file (one input per line) or a string of one or
        more inputs separated by newlines or commas.

    Returns
    -------
    list
        The parsed, whitespace-stripped inputs with empties removed.
    """
    if os.path.isfile(input_data):
        logger.info(f"Reading inputs from file {input_data}")
        with open(input_data) as f:
            lines = f.readlines()
    else:
        logger.info("Interpreting input as a delimited string")
        lines = re.split(r"[\n,]", input_data)
    return [line.strip() for line in lines if line.strip()]


def _run_in_chunks(
    mdl: Model,
    model_id: str,
    inputs: list,
    output_path: str | None,
    on_progress: Callable[..., None] | None,
) -> tuple:
    """
    Predict ``inputs`` in chunks, appending each result to the output CSV.

    Results are written to ``<output>.partial`` and moved into place only when
    every chunk succeeded, so a failure never leaves a half-written results
    file. Writing as we go also keeps only one chunk in memory.

    Parameters
    ----------
    mdl : Model
        The served model.
    model_id : str
        Model identifier, used to name a temporary output file.
    inputs : list
        All inputs to predict on.
    output_path : str, optional
        Where to write the results CSV; a temporary file is used if omitted.
    on_progress : callable, optional
        Called as ``on_progress(done, total, message)`` before the first chunk
        and after each one.

    Returns
    -------
    tuple
        ``(output_path, num_rows, columns)``.

    Raises
    ------
    ValueError
        If the model returns different columns for different chunks.
    """
    total = len(inputs)
    created_temp = output_path is None
    if created_temp:
        fd, output_path = tempfile.mkstemp(prefix=f"{model_id}_", suffix=".csv")
        os.close(fd)
    partial = f"{output_path}.partial"
    columns = None
    rows = 0
    try:
        if on_progress:
            on_progress(0, total, f"0/{total} inputs")
        for start in range(0, total, CHUNK_SIZE):
            chunk = inputs[start : start + CHUNK_SIZE]
            df = mdl.run(chunk)
            if columns is None:
                columns = list(df.columns)
            elif list(df.columns) != columns:
                raise ValueError(
                    f"The model returned different columns for chunk starting at "
                    f"input {start}: {list(df.columns)} instead of {columns}"
                )
            df.to_csv(
                partial, mode="a" if start else "w", header=not start, index=False
            )
            rows += len(df)
            done = start + len(chunk)
            logger.info(f"Predicted {done}/{total} inputs with model {model_id}")
            if on_progress:
                on_progress(done, total, f"{done}/{total} inputs")
        os.replace(partial, output_path)
    except BaseException:
        for path in (partial, output_path if created_temp else None):
            if path and os.path.exists(path):
                os.remove(path)
        raise
    return output_path, rows, columns


def predict_helper(
    model_id: str,
    input_data: str,
    output_path: str | None = None,
    on_progress: Callable[..., None] | None = None,
) -> dict:
    """
    Run predictions for a served model and write the results to a CSV file.

    Up to ``CHUNK_SIZE`` inputs run in a single call. Larger sets run in chunks
    so that progress can be reported.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_data : str
        Either a path to a file (one input per line) or a string of one or
        more inputs separated by newlines or commas.
    output_path : str, optional
        Where to write the results CSV. If omitted, a temporary file is created.
    on_progress : callable, optional
        Called as ``on_progress(done, total, message)`` while a large set runs.

    Returns
    -------
    dict
        On success, ``status`` is ``"ok"`` with the ``output_path``, the
        ``num_predictions`` and the result ``columns``. On failure, ``status``
        is ``"error"`` with an ``error`` message.
    """
    try:
        log_conda_environment()
        inputs = parse_input(input_data)
        if not inputs:
            logger.error("No valid inputs found to predict on")
            return error_result("No valid inputs provided")

        logger.info(f"Running {len(inputs)} prediction(s) with model {model_id}")
        mdl = Model(model_id=model_id, verbose=True)

        if len(inputs) > CHUNK_SIZE:
            output_path, num_rows, columns = _run_in_chunks(
                mdl, model_id, inputs, output_path, on_progress
            )
        else:
            df = mdl.run(inputs)
            if output_path is None:
                fd, output_path = tempfile.mkstemp(prefix=f"{model_id}_", suffix=".csv")
                os.close(fd)
            df.to_csv(output_path, index=False)
            num_rows, columns = len(df), list(df.columns)

        logger.success(f"Wrote {num_rows} prediction(s) to {output_path}")
        return {
            "status": "ok",
            "output_path": output_path,
            "num_predictions": num_rows,
            "columns": columns,
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Encountered an error while predicting with {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return error_result(e)
