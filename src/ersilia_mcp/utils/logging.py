"""Logging utilities for the Ersilia MCP server.

Exposes a module-level :data:`logger` singleton built on the standard library
``logging`` module and Rich's :class:`~rich.logging.RichHandler`. In addition
to the usual levels, it provides a :meth:`ErsiliaLogger.success` method for
reporting successful outcomes.
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from ersilia_mcp.default import EOS_MCP

SUCCESS = 25
LOGS_DIR = "logs"
LOG_FILENAME = "ersilia-mcp.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logging.addLevelName(SUCCESS, "SUCCESS")


class ErsiliaLogger(logging.Logger):
    """A :class:`logging.Logger` with an extra ``success`` level."""

    def success(self, msg: str, *args, **kwargs) -> None:
        """Log a message at the custom ``SUCCESS`` level (between INFO and WARNING)."""
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)

    def log_to_file(self):
        """
        Configure the logger to write to a file in the logs/ directory.

        Creates a logs/ directory in EOS_MCP if it doesn't exist and adds a TimedRotatingFileHandler
        to write logs to ersilia-mcp.log. Rotates daily at midnight and keeps 7 days of logs.

        Returns
        -------
        Path
            The path to the log file.
        """
        log_dir_path = Path(EOS_MCP) / LOGS_DIR  # $HOME/eos/mcp/logs
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_filepath = log_dir_path / LOG_FILENAME

        file_handler = TimedRotatingFileHandler(
            log_filepath, when="midnight", interval=1, backupCount=7
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.addHandler(file_handler)

        return log_filepath


def log_conda_environment() -> None:
    """Log the active conda environment and Python interpreter for debugging."""
    logger.debug(f"CONDA_DEFAULT_ENV={os.environ.get('CONDA_DEFAULT_ENV')}")
    logger.debug(f"CONDA_PREFIX={os.environ.get('CONDA_PREFIX')}")
    logger.debug(f"sys.executable={sys.executable}")
    logger.debug(f"sys.prefix={sys.prefix}")


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
