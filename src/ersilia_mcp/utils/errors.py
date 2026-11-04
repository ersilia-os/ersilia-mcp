"""Structured error results shared by the Ersilia model tools."""


def error_message(exc: BaseException) -> str:
    """
    Build a readable error message for a tool response.

    Ersilia can signal failures with ``sys.exit`` after logging the cause, so
    ``str(exc)`` for a ``SystemExit`` is just the exit code.

    Parameters
    ----------
    exc : BaseException
        The exception (or ``SystemExit``) that was caught.

    Returns
    -------
    str
        ``str(exc)`` (or the exception class name when it is empty) for
        ordinary exceptions; for ``SystemExit`` a message pointing to the MCP
        server log (``~/eos/mcp/logs``) for details.
    """
    if isinstance(exc, SystemExit):
        return (
            f"Process exited with code {exc.code}; check the MCP server log "
            "in ~/eos/mcp/logs for the cause"
        )
    return str(exc) or type(exc).__name__


def error_result(message: str | BaseException) -> dict:
    """
    Build the ``{"status": "error", ...}`` dict returned when a tool fails.

    Parameters
    ----------
    message : str or BaseException
        A description of the failure, or the exception that caused it.

    Returns
    -------
    dict
        ``{"status": "error", "error": <message>}``.
    """
    if isinstance(message, BaseException):
        message = error_message(message)
    return {"status": "error", "error": message}
