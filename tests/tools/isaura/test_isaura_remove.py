"""Tests for the remove_from_isaura tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_REMOVE = "ersilia_mcp.utils.isaura.isaura_operations.remove"
_TOOL = "remove_from_isaura"


def test_remove_tool_success():
    """Test the tool returns the removal summary and forwards every argument."""
    with patch(_REMOVE) as mock_remove:
        mock_response = {
            "status": "ok",
            "num_requested": 2,
            "num_removed": 1,
            "num_not_found": 1,
        }
        mock_remove.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                _TOOL,
                {
                    "model": "eos3b5e",
                    "input_data": "CCO,CCC",
                    "bucket": "myproject",
                    "version": "v2",
                },
            )
        )
        assert result.structured_content == mock_response
        mock_remove.assert_called_once_with("eos3b5e", "CCO,CCC", "myproject", "v2")


def test_remove_tool_defaults_version():
    """Test the tool defaults the version to v1."""
    with patch(_REMOVE) as mock_remove:
        mock_remove.return_value = {"status": "ok"}
        asyncio.run(
            mcp.call_tool(
                _TOOL,
                {"model": "eos3b5e", "input_data": "CCO", "bucket": "myproject"},
            )
        )
        mock_remove.assert_called_once_with("eos3b5e", "CCO", "myproject", "v1")


def test_remove_tool_error():
    """Test the tool passes through an error status."""
    with patch(_REMOVE) as mock_remove:
        mock_remove.return_value = {"status": "error", "error": "no index"}
        result = asyncio.run(
            mcp.call_tool(
                _TOOL,
                {"model": "eos3b5e", "input_data": "CCO", "bucket": "myproject"},
            )
        )
        assert result.structured_content["status"] == "error"
