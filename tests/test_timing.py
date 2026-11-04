"""Tests that tool calls are timed and logged."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp
from ersilia_mcp.utils.logging import logger


def test_tool_call_duration_is_logged(caplog):
    """Test a tool call logs its name and duration through the project logger."""
    # The project logger does not propagate to the root logger, so attach
    # caplog's handler to it directly.
    logger.addHandler(caplog.handler)
    try:
        with patch("ersilia_mcp.tools.search.search_catalog", return_value="ok"):
            asyncio.run(mcp.call_tool("search_model", {"query": "malaria"}))
    finally:
        logger.removeHandler(caplog.handler)

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        m.startswith("Tool 'search_model' completed in") and m.endswith("ms")
        for m in messages
    ), messages
