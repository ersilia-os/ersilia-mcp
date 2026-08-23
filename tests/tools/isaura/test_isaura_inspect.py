"""Tests for the check_cache tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_INSPECT = "ersilia_mcp.utils.isaura.isaura_operations.inspect"


def test_check_cache_tool_success():
    """Test the check_cache tool returns the inspection summary."""
    with patch(_INSPECT) as mock_inspect:
        mock_response = {
            "status": "ok",
            "num_requested": 3,
            "num_cached": 2,
            "num_missing": 1,
            "cached": ["CCO", "CCC"],
            "missing": ["CCCC"],
        }
        mock_inspect.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                "check_cache",
                {
                    "model": "eos3b5e",
                    "input_data": "CCO,CCC,CCCC",
                    "version": "v2",
                    "bucket": "isaura-private",
                },
            )
        )
        assert result.structured_content == mock_response
        mock_inspect.assert_called_once_with(
            "eos3b5e", "CCO,CCC,CCCC", "v2", "isaura-private"
        )


def test_check_cache_tool_error():
    """Test the check_cache tool passes through an error status."""
    with patch(_INSPECT) as mock_inspect:
        mock_inspect.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool("check_cache", {"model": "eos3b5e", "input_data": "CCO"})
        )
        assert result.structured_content["status"] == "error"
