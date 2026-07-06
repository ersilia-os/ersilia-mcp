"""Tests for the search_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_search_model_tool():
    """Test the search_model tool is registered and callable with query."""
    with patch("ersilia_mcp.tools.search.search_catalog") as mock_search:
        mock_search.return_value = "eos4zfy  maip-malaria — MAIP test (score: 12.0)"
        result = asyncio.run(mcp.call_tool("search_model", {"query": "malaria"}))
        assert (
            result.structured_content["result"]
            == "eos4zfy  maip-malaria — MAIP test (score: 12.0)"
        )
        mock_search.assert_called_once_with("malaria")
