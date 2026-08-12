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
# Cap the ``missing`` list returned to callers so the payload stays small.
_MAX_MISSING_REPORTED = 20


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
        return [row[column].strip() for row in reader if (row.get(column) or "").strip()]


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
        if os.path.isfile(input_data):
            source_csv = input_data
            requested = _csv_inputs(input_data)
        else:
            requested = [s.strip() for s in input_data.split(",") if s.strip()]
            source_csv = None

        if not requested:
            logger.error("No valid inputs found to read")
            return {"status": "error", "error": "No valid inputs provided"}

        if source_csv is None:
            source_csv = temp_input_csv = _write_input_csv(requested)

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
            "missing": missing[:_MAX_MISSING_REPORTED],
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
