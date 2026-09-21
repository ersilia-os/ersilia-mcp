"""Tests for the get_precalculations tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_READ = "ersilia_mcp.utils.isaura.isaura_operations.read"


def test_get_precalculations_tool_success():
    """Test the get_precalculations tool returns the read summary."""
    with patch(_READ) as mock_read:
        mock_response = {
            "status": "ok",
            "num_requested": 2,
            "num_cached": 2,
            "num_missing": 0,
            "missing": [],
            "output_path": "/tmp/eos3b5e_abc.csv",
            "columns": ["input", "value"],
        }
        mock_read.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                "get_precalculations",
                {
                    "model": "eos3b5e",
                    "input_data": "CCO,CCC",
                    "version": "v2",
                    "bucket": "isaura-private",
                    "output_path": "/data/out.csv",
                },
            )
        )
        assert result.structured_content == mock_response
        mock_read.assert_called_once_with(
            "eos3b5e", "CCO,CCC", "v2", "isaura-private", "/data/out.csv"
        )


def test_get_precalculations_tool_error():
    """Test the get_precalculations tool passes through an error status."""
    with patch(_READ) as mock_read:
        mock_read.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool(
                "get_precalculations", {"model": "eos3b5e", "input_data": "CCO"}
            )
        )
        assert result.structured_content["status"] == "error"
