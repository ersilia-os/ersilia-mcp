"""Tests for the write_precalculations_to_isaura tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_WRITE = "ersilia_mcp.utils.isaura.isaura_operations.write"
_TOOL = "write_precalculations_to_isaura"


def test_write_precalculations_tool_success():
    """Test the tool returns the write summary and forwards every argument."""
    with patch(_WRITE) as mock_write:
        mock_response = {
            "status": "ok",
            "num_rows": 2,
            "columns": ["key", "input", "value"],
        }
        mock_write.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                _TOOL,
                {
                    "model": "eos3b5e",
                    "input_csv": "/data/results.csv",
                    "version": "v2",
                    "bucket": "isaura-private",
                },
            )
        )
        assert result.structured_content == mock_response
        mock_write.assert_called_once_with(
            "eos3b5e", "/data/results.csv", "v2", "isaura-private"
        )


def test_write_precalculations_tool_error():
    """Test the tool passes through an error status."""
    with patch(_WRITE) as mock_write:
        mock_write.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool(_TOOL, {"model": "eos3b5e", "input_csv": "/data/results.csv"})
        )
        assert result.structured_content["status"] == "error"
