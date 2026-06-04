"""Logging utilities for the Ersilia MCP server.

Exposes a module-level :data:`logger` singleton built on the standard library
``logging`` module and Rich's :class:`~rich.logging.RichHandler`. In addition
to the usual levels, it provides a :meth:`ErsiliaLogger.success` method for
reporting successful outcomes.
"""

import logging

from rich.logging import RichHandler

SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")


class ErsiliaLogger(logging.Logger):
    """A :class:`logging.Logger` with an extra ``success`` level."""

    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a message at the custom ``SUCCESS`` level (between INFO and WARNING)."""
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)


def _build_logger() -> ErsiliaLogger:
    logging.setLoggerClass(ErsiliaLogger)
    log = logging.getLogger("ersilia_mcp")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        log.addHandler(handler)
    log.propagate = False
    return log


logger: ErsiliaLogger = _build_logger()
