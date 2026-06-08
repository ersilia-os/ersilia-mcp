"""Tests for the search_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_search_model_tool():
    """Test the search_model tool is registered and callable."""
    with patch("ersilia_mcp.tools.search.fetch_catalog") as mock_fetch:
        mock_fetch.return_value = "eos4zfy  maip-malaria — MAIP test"
        _, structured = asyncio.run(mcp.call_tool("search_model", {}))
        assert structured["result"] == "eos4zfy  maip-malaria — MAIP test"
        mock_fetch.assert_called_once()
