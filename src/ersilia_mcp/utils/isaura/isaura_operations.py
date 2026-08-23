"""Check availability of and retrieve precalculated model results from Isaura.

The public :func:`read` first *inspects* which inputs are already cached and
then retrieves only that subset. This avoids ``IsauraReader``'s exact-mode
behaviour of aborting (``sys.exit``) when any requested input is missing, and
lets us report per-request availability instead of an all-or-nothing result.
"""

import csv
import os
import tempfile
import traceback

from isaura.manage import IsauraInspect, IsauraReader

from ersilia_mcp.utils.logging import logger

# Columns Isaura accepts as the molecule/lookup key, in priority order.
_INPUT_COLUMNS = ("input", "smiles")
# Cap the input lists returned to callers so the payload stays small.
_MAX_REPORTED = 20


def _write_input_csv(inputs: list) -> str:
    """
    Write inputs to a temporary CSV with a single ``input`` column.

    Parameters
    ----------
    inputs : list
        The inputs (e.g. SMILES) to look up in the Isaura store.

    Returns
    -------
    str
        Path to the temporary CSV file.
    """
    fd, path = tempfile.mkstemp(prefix="isaura_inputs_", suffix=".csv")
    with os.fdopen(fd, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["input"])
        writer.writerows([[value] for value in inputs])
    return path


def _csv_inputs(csv_path: str) -> list:
    """
    Read the ``input``/``smiles`` column values from a CSV.

    Parameters
    ----------
    csv_path : str
        Path to a CSV with an ``input`` or ``smiles`` column.

    Returns
    -------
    list
        The molecule values in the column.

    Raises
    ------
    ValueError
        If the CSV has neither an ``input`` nor a ``smiles`` column.
    """
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        column = next(
            (c for c in _INPUT_COLUMNS if c in (reader.fieldnames or [])), None
        )
        if column is None:
            raise ValueError(
                f"CSV must have an 'input' or 'smiles' column; "
                f"found {reader.fieldnames}"
            )
        return [
            row[column].strip() for row in reader if (row.get(column) or "").strip()
        ]


def _resolve_inputs(input_data: str) -> tuple:
    """
    Turn the tool input into requested inputs and a CSV Isaura can read.

    Parameters
    ----------
    input_data : str
        Either a path to a CSV with an ``input``/``smiles`` column, or a
        comma-separated string of inputs.

    Returns
    -------
    tuple
        ``(requested, source_csv, temp_input_csv)`` where ``requested`` is the
        list of parsed inputs, ``source_csv`` is a CSV path Isaura can read
        (``None`` when there are no inputs), and ``temp_input_csv`` is a path
        the caller must delete (``None`` when a user-supplied CSV was reused).
    """
    if os.path.isfile(input_data):
        return _csv_inputs(input_data), input_data, None
    requested = [s.strip() for s in input_data.split(",") if s.strip()]
    if not requested:
        return [], None, None
    temp_input_csv = _write_input_csv(requested)
    return requested, temp_input_csv, temp_input_csv


def _inspect_cached(model_id: str, version: str, bucket: str, input_csv: str) -> list:
    """
    Return the subset of the inputs in ``input_csv`` that Isaura has cached.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    version : str
        Model version.
    bucket : str
        Project bucket to inspect.
    input_csv : str
        Path to a CSV with an ``input`` column.

    Returns
    -------
    list
        The cached inputs (may be empty).
    """
    inspector = IsauraInspect(
        model_id=model_id,
        model_version=version,
        cloud=False,
        project_name=bucket,
    )
    available = inspector.inspect_inputs(input_csv=input_csv)
    column = next((c for c in _INPUT_COLUMNS if c in available.columns), None)
    if column is None:
        return []
    return [str(v) for v in available[column]]


def read(
    model_id: str,
    input_data: str,
    version: str = "v1",
    bucket: str = "isaura-public",
    output_path: str | None = None,
) -> dict:
    """
    Check which inputs are cached in Isaura and retrieve those results.

    Inputs are first inspected for availability; only the cached subset is
    retrieved. Missing inputs are reported rather than causing the read to fail.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_data : str
        Either a path to a CSV with an ``input``/``smiles`` column (passed
        straight to Isaura), or a comma-separated string of inputs.
    version : str, optional
        Model version to read, by default ``"v1"``.
    bucket : str, optional
        Project bucket to read from, by default ``"isaura-public"``.
    output_path : str, optional
        Where to write the retrieved results CSV. Only written when at least
        one input is cached; if omitted, a temporary file is created.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_requested": int,
                "num_cached": int,
                "num_missing": int,
                "missing": list,      # up to 20 inputs not cached
                "output_path": str | None,  # None when nothing was cached
                "columns": list,
            }

        On failure (e.g. the local store is unreachable)::

            {"status": "error", "error": str}
    """
    # Temp CSVs we create (and must clean up); a user-supplied CSV is left alone.
    temp_input_csv = None
    subset_csv = None
    try:
        requested, source_csv, temp_input_csv = _resolve_inputs(input_data)
        if not requested:
            logger.error("No valid inputs found to read")
            return {"status": "error", "error": "No valid inputs provided"}

        logger.info(
            f"Inspecting {len(requested)} input(s) of model {model_id} "
            f"({version}) in bucket {bucket}"
        )
        cached = _inspect_cached(model_id, version, bucket, source_csv)
        cached_set = set(cached)
        missing = [value for value in requested if value not in cached_set]
        logger.info(f"{len(cached)} cached, {len(missing)} missing")

        result = {
            "status": "ok",
            "num_requested": len(requested),
            "num_cached": len(cached),
            "num_missing": len(missing),
            "missing": missing[:_MAX_REPORTED],
            "output_path": None,
            "columns": [],
        }
        if not cached:
            return result

        # Read only the cached inputs so a missing one can't abort the read.
        # When nothing is missing, ``source_csv`` already holds exactly those.
        if missing:
            read_csv = subset_csv = _write_input_csv(cached)
        else:
            read_csv = source_csv
        with IsauraReader(
            model_id=model_id,
            model_version=version,
            input_csv=read_csv,
            approximate=False,
            bucket=bucket,
        ) as reader:
            # Call without ``output_csv``: that path returns an empty frame and
            # writes to disk instead, so we take the frame and write it here.
            df = reader.read()

        if output_path is None:
            fd, output_path = tempfile.mkstemp(prefix=f"{model_id}_", suffix=".csv")
            os.close(fd)
        df.to_csv(output_path, index=False)

        logger.success(
            f"Retrieved {len(df)} precalculated result(s) for {model_id}; "
            f"wrote to {output_path}"
        )
        result["output_path"] = output_path
        result["columns"] = list(df.columns)
        return result
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error reading precalculations for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
    finally:
        for path in (temp_input_csv, subset_csv):
            if path is not None and os.path.exists(path):
                os.remove(path)


def inspect(
    model_id: str,
    input_data: str,
    version: str = "v1",
    bucket: str = "isaura-public",
) -> dict:
    """
    Report which inputs are cached in Isaura without retrieving their results.

    This is the inspection half of :func:`read`: it looks up availability but
    does not fetch or write any results, so it is a cheap way to see how much
    of a workload can be served from the cache.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_data : str
        Either a path to a CSV with an ``input``/``smiles`` column, or a
        comma-separated string of inputs.
    version : str, optional
        Model version to inspect, by default ``"v1"``.
    bucket : str, optional
        Project bucket to inspect, by default ``"isaura-public"``.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_requested": int,
                "num_cached": int,
                "num_missing": int,
                "cached": list,   # up to 20 inputs that are cached
                "missing": list,  # up to 20 inputs that are not cached
            }

        On failure (e.g. the local store is unreachable)::

            {"status": "error", "error": str}
    """
    temp_input_csv = None
    try:
        requested, source_csv, temp_input_csv = _resolve_inputs(input_data)
        if not requested:
            logger.error("No valid inputs found to inspect")
            return {"status": "error", "error": "No valid inputs provided"}

        logger.info(
            f"Inspecting {len(requested)} input(s) of model {model_id} "
            f"({version}) in bucket {bucket}"
        )
        cached = _inspect_cached(model_id, version, bucket, source_csv)
        cached_set = set(cached)
        missing = [value for value in requested if value not in cached_set]
        logger.info(f"{len(cached)} cached, {len(missing)} missing")

        return {
            "status": "ok",
            "num_requested": len(requested),
            "num_cached": len(cached),
            "num_missing": len(missing),
            "cached": cached[:_MAX_REPORTED],
            "missing": missing[:_MAX_REPORTED],
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error inspecting cache for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
    finally:
        if temp_input_csv is not None and os.path.exists(temp_input_csv):
            os.remove(temp_input_csv)
