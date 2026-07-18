"""Run predictions against served Ersilia models."""

import os
import re
import tempfile
import traceback

from ersilia.api import Model

from ersilia_mcp.utils.logging import logger, log_conda_environment


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


def predict_helper(model_id: str, input_data: str, output_path: str = None) -> dict:
    """
    Run predictions for a served model and write the results to a CSV file.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_data : str
        Either a path to a file (one input per line) or a string of one or
        more inputs separated by newlines or commas.
    output_path : str, optional
        Where to write the results CSV. If omitted, a temporary file is created.

    Returns
    -------
    dict
        A summary containing the ``output_path``, the number of predictions, and
        the result ``columns``, or an empty dict if prediction failed.
    """
    try:
        log_conda_environment()
        inputs = parse_input(input_data)
        if not inputs:
            logger.error("No valid inputs found to predict on")
            return {}

        logger.info(f"Running {len(inputs)} prediction(s) with model {model_id}")
        mdl = Model(model_id=model_id, verbose=True)
        df = mdl.run(inputs)

        if output_path is None:
            fd, output_path = tempfile.mkstemp(prefix=f"{model_id}_", suffix=".csv")
            os.close(fd)
        df.to_csv(output_path, index=False)

        logger.success(f"Wrote {len(df)} prediction(s) to {output_path}")
        return {
            "output_path": output_path,
            "num_predictions": len(df),
            "columns": list(df.columns),
        }
    except (Exception, SystemExit) as e:
        logger.error(f"Encountered an error while predicting with {model_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {}
