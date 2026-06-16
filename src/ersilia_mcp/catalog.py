"""Fetch and format the Ersilia model hub catalog."""

from ersilia_mcp.utils.logging import logger

from ersilia.api.commands.catalog import catalog


def format_catalog(data: object) -> str:
    """Render the catalog as compact ``identifier  slug — title`` lines.

    Parameters
    ----------
    data : object
        Catalog records (list of dicts with Identifier, Slug, Title keys).

    Returns
    -------
    str
        One line per model, format: ``identifier  slug — title``.
        Returns empty string if no recognisable records are found.
    """
    if not isinstance(data, list):
        return ""
    lines = []
    for record in data:
        if not isinstance(record, dict):
            continue
        identifier = record.get("Identifier")
        slug = record.get("Slug")
        if not identifier or not slug:
            continue
        title = record.get("Title")
        line = f"{identifier}  {slug}"
        if title:
            line += f" — {title}"
        lines.append(line)
    logger.info("Formatted %d of %d models", len(lines), len(data))
    return "\n".join(lines)


def fetch_catalog() -> str:
    """Fetch the hub catalog as compact text via the Ersilia Python API.

    Calls the Ersilia API to fetch the model hub catalog and returns it as
    compact ``identifier  slug — title`` lines.

    Returns a human-readable message on failure.
    """
    try:
        df = catalog(hub=True, more=True)
        if df is None:
            logger.warning("Failed to fetch catalog from hub.")
            return "Failed to fetch catalog from hub."
        # Convert DataFrame to list of dicts for formatting
        data = df.to_dict("records")
        logger.success("Fetched %d models from Ersilia model hub", len(data))
        return format_catalog(data) or "No models found in catalog."
    except Exception as exc:
        logger.error("Failed to fetch catalog: %s", exc)
        return f"Failed to fetch catalog: {exc}"
