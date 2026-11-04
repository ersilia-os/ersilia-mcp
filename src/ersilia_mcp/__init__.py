"""Model Context Protocol server for the Ersilia Model Hub."""

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth is ``[project].version`` in pyproject.toml.
    __version__ = version("ersilia-mcp")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "unknown"
