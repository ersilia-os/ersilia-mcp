"""Tests for the inspect_isaura_cache tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_INSPECT = "ersilia_mcp.utils.isaura.isaura_operations.inspect"


def test_inspect_isaura_cache_tool_success():
    """Test the inspect_isaura_cache tool returns the inspection summary."""
    with patch(_INSPECT) as mock_inspect:
        mock_response = {
            "status": "ok",
            "num_requested": 3,
            "num_cached": 2,
            "num_missing": 1,
        }
        mock_inspect.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                "inspect_isaura_cache",
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
            "eos3b5e", "CCO,CCC,CCCC", "v2", "isaura-private", False
        )


def test_inspect_isaura_cache_tool_forwards_verbose():
    """Test the inspect_isaura_cache tool forwards verbose and returns the input lists."""
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
                "inspect_isaura_cache",
                {
                    "model": "eos3b5e",
                    "input_data": "CCO,CCC,CCCC",
                    "verbose": True,
                },
            )
        )
        assert result.structured_content == mock_response
        mock_inspect.assert_called_once_with(
            "eos3b5e", "CCO,CCC,CCCC", "v1", "isaura-public", True
        )


def test_inspect_isaura_cache_tool_error():
    """Test the inspect_isaura_cache tool passes through an error status."""
    with patch(_INSPECT) as mock_inspect:
        mock_inspect.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool("inspect_isaura_cache", {"model": "eos3b5e", "input_data": "CCO"})
        )
        assert result.structured_content["status"] == "error"
