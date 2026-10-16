"""Helper functions used to interact with the Isaura store."""

import csv
import os
import tempfile
import traceback

from isaura.manage import (
    IsauraCopy,
    IsauraInspect,
    IsauraMolRemover,
    IsauraReader,
    IsauraWriter,
)

from ersilia_mcp.utils.logging import logger

# Columns Isaura accepts as the molecule/lookup key, in priority order.
_INPUT_COLUMNS = ("input", "smiles")


def _error_message(exc: BaseException) -> str:
    """
    Build a readable error message for the tool response.

    Isaura signals some failures (e.g. a missing bucket) with ``sys.exit(1)``
    after logging the cause, so ``str(exc)`` is just the exit code.

    Parameters
    ----------
    exc : BaseException
        The exception (or ``SystemExit``) that was caught.

    Returns
    -------
    str
        ``str(exc)`` for ordinary exceptions; for ``SystemExit`` a message
        pointing to the MCP server log (``~/eos/mcp/logs``) for details.
    """
    if isinstance(exc, SystemExit):
        return (
            f"Isaura exited with code {exc.code}; check the MCP server log "
            "in ~/eos/mcp/logs for the cause (e.g. the bucket or model "
            "version does not exist)"
        )
    return str(exc)


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
        string of inputs separated by commas or newlines.

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
    requested = [s.strip() for s in input_data.replace("\n", ",").split(",")]
    requested = [s for s in requested if s]
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
    verbose: bool = False,
) -> dict:
    """
    Check which inputs are cached in Isaura and retrieve those results.

    Inputs are first inspected for availability; only the cached subset is
    retrieved. Missing inputs are counted rather than causing the read to fail.

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
    verbose : bool, optional
        When ``True``, also return the full list of inputs that were not
        cached. By default only the counts are returned.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_requested": int,
                "num_cached": int,
                "num_missing": int,
                "output_path": str | None,  # None when nothing was cached
                "columns": list,
                # only present when verbose=True:
                "missing": list,  # every input not cached
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
            "output_path": None,
            "columns": [],
        }
        if verbose:
            result["missing"] = missing
        if not cached:
            return result

        # Write the cached inputs to a temp csv file.
        # Since we pass approximate=False and since the mcp server runs on stdio,
        # un-cached inputs will cause the read to error.
        # When everything is cached in isaura, we can use ``source_csv`` directly.
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
        return {"status": "error", "error": _error_message(e)}
    finally:
        for path in (temp_input_csv, subset_csv):
            if path is not None and os.path.exists(path):
                os.remove(path)


def write(
    model_id: str,
    input_csv: str,
    version: str = "v1",
    bucket: str = "isaura-public",
) -> dict:
    """
    Store a model's results in Isaura so they can be read back later.

    Unlike :func:`read` and :func:`inspect`, this takes a results CSV rather
    than a list of inputs: Isaura keys each row on its ``input``/``smiles``
    value and stores the remaining columns as the payload.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_csv : str
        Path to a results CSV with an ``input``/``smiles`` column plus the
        model's output columns — e.g. the file written by the ``predict`` tool.
        If the file name contains a model identifier that disagrees with
        ``model_id``, Isaura refuses the write.
    version : str, optional
        Model version to write under, by default ``"v1"``.
    bucket : str, optional
        Project bucket to write to, by default ``"isaura-public"``.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_rows": int,   # rows submitted, before deduplication
                "columns": list,   # the CSV's columns
            }

        Isaura skips rows whose input is already stored, so ``num_rows``
        counts what was submitted rather than what was newly added.

        On failure (e.g. the local store is unreachable)::

            {"status": "error", "error": str}
    """
    try:
        if not os.path.isfile(input_csv):
            logger.error(f"No such results CSV: {input_csv}")
            return {"status": "error", "error": f"No such file: {input_csv}"}

        with open(input_csv, newline="") as f:
            columns = csv.DictReader(f).fieldnames or []
        # Raises when neither an 'input' nor a 'smiles' column is present.
        rows = _csv_inputs(input_csv)
        if not rows:
            logger.error(f"No inputs to write in {input_csv}")
            return {"status": "error", "error": "No valid inputs provided"}

        logger.info(
            f"Writing {len(rows)} row(s) of model {model_id} "
            f"({version}) to bucket {bucket}"
        )
        with IsauraWriter(
            input_csv=input_csv,
            model_id=model_id,
            model_version=version,
            bucket=bucket,
        ) as writer:
            writer.write()

        logger.success(
            f"Wrote {len(rows)} row(s) for {model_id} ({version}) to {bucket}"
        )
        return {
            "status": "ok",
            "num_rows": len(rows),
            "columns": list(columns),
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error writing precalculations for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}


def inspect(
    model_id: str,
    input_data: str,
    version: str = "v1",
    bucket: str = "isaura-public",
    verbose: bool = False,
) -> dict:
    """
    Report which inputs are cached in Isaura without retrieving their results.

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
    verbose : bool, optional
        When ``True``, include the full ``cached`` and ``missing`` input lists
        in the result. By default only the counts are returned.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_requested": int,
                "num_cached": int,
                "num_missing": int,
                # only present when verbose=True:
                "cached": list,   # every cached input
                "missing": list,  # every input not cached
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

        result = {
            "status": "ok",
            "num_requested": len(requested),
            "num_cached": len(cached),
            "num_missing": len(missing),
        }
        if verbose:
            result["cached"] = cached
            result["missing"] = missing
        return result
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error inspecting cache for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": _error_message(e)}
    finally:
        if temp_input_csv is not None and os.path.exists(temp_input_csv):
            os.remove(temp_input_csv)


def persist(model_id: str, bucket: str, version: str = "v1") -> dict:
    """
    Route rows from a project bucket into ``isaura-public``/``isaura-private``.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    bucket : str
        Project bucket to persist from.
    version : str, optional
        Model version, by default ``"v1"``.

    Returns
    -------
    dict
        On success::

            {"status": "ok", "model": str, "version": str, "bucket": str}

        On failure::

            {"status": "error", "error": str}
    """
    try:
        logger.info(f"Persisting model {model_id} ({version}) from bucket {bucket}")
        IsauraCopy(model_id=model_id, model_version=version, bucket=bucket).copy()
        logger.success(f"Persisted {model_id} ({version}) from bucket {bucket}")
        return {
            "status": "ok",
            "model": model_id,
            "version": version,
            "bucket": bucket,
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error persisting {model_id} from {bucket}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": _error_message(e)}


def remove(
    model_id: str,
    input_data: str,
    bucket: str,
    version: str = "v1",
) -> dict:
    """
    Remove specific inputs from a model/version stored in a bucket.

    Parameters
    ----------
    model_id : str
        Model identifier (e.g., ``eos3b5e``).
    input_data : str
        Either a path to a CSV with an ``input``/``smiles`` column, or a string
        of inputs separated by commas or newlines.
    bucket : str
        Project bucket to remove from.
    version : str, optional
        Model version, by default ``"v1"``.

    Returns
    -------
    dict
        On success::

            {
                "status": "ok",
                "num_requested": int,
                "num_removed": int,
                "num_not_found": int,
            }

        On failure::

            {"status": "error", "error": str}
    """
    temp_input_csv = None
    try:
        requested, source_csv, temp_input_csv = _resolve_inputs(input_data)
        if not requested:
            logger.error("No valid inputs found to remove")
            return {"status": "error", "error": "No valid inputs provided"}

        logger.info(
            f"Removing {len(requested)} input(s) of model {model_id} "
            f"({version}) from bucket {bucket}"
        )
        # show_progress=False: the Rich progress bar must not write to stdio.
        with IsauraMolRemover(
            model_id=model_id,
            model_version=version,
            bucket=bucket,
            input_csv=source_csv,
        ) as remover:
            n_removed, n_not_found = remover.remove(show_progress=False)

        logger.success(f"Removed {n_removed} row(s); {n_not_found} not found")
        return {
            "status": "ok",
            "num_requested": len(requested),
            "num_removed": n_removed,
            "num_not_found": n_not_found,
        }
    except (Exception, SystemExit) as e:  # noqa: BLE001
        logger.error(f"Error removing inputs for {model_id}: {e!s}")
        logger.error(traceback.format_exc())
        return {"status": "error", "error": _error_message(e)}
    finally:
        if temp_input_csv is not None and os.path.exists(temp_input_csv):
            os.remove(temp_input_csv)
