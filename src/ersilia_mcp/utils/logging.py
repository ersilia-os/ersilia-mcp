"""Logging utilities for the Ersilia MCP server.

Exposes a module-level :data:`logger` singleton built on the standard library
``logging`` module and Rich's :class:`~rich.logging.RichHandler`. In addition
to the usual levels, it provides a :meth:`ErsiliaLogger.success` method for
reporting successful outcomes.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

SUCCESS = 25
LOGS_DIR = "logs"
LOG_FILENAME = "ersilia-mcp.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logging.addLevelName(SUCCESS, "SUCCESS")


def _get_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: assume standard layout (src/package/utils/logging.py)
    return current.parents[3]


class ErsiliaLogger(logging.Logger):
    """A :class:`logging.Logger` with an extra ``success`` level."""

    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a message at the custom ``SUCCESS`` level (between INFO and WARNING)."""
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)

    def log_to_file(self):
        """
        Configure the logger to write to a file in the logs/ directory.

        Creates a logs/ directory if it doesn't exist and adds a TimedRotatingFileHandler
        to write logs to ersilia-mcp.log. Rotates daily at midnight and keeps 7 days of logs.

        Returns
        -------
        Path
            The path to the log file.
        """
        log_dir_path = _get_project_root() / LOGS_DIR
        log_dir_path.mkdir(exist_ok=True)
        log_filepath = log_dir_path / LOG_FILENAME

        file_handler = TimedRotatingFileHandler(
            log_filepath, when="midnight", interval=1, backupCount=7
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.addHandler(file_handler)

        return log_filepath


def _build_logger() -> ErsiliaLogger:
    logging.setLoggerClass(ErsiliaLogger)
    log = logging.getLogger("ersilia_mcp")
    log.setLevel(logging.INFO)
    if not log.handlers:
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        log.addHandler(handler)
    log.propagate = False
    log.log_to_file()
    return log


logger: ErsiliaLogger = _build_logger()
