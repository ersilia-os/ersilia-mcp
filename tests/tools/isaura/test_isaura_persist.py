"""Tests for the persist_isaura_data tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_PERSIST = "ersilia_mcp.utils.isaura.isaura_operations.persist"
_TOOL = "persist_isaura_data"


def test_persist_tool_success():
    """Test the tool returns the persist summary and forwards every argument."""
    with patch(_PERSIST) as mock_persist:
        mock_response = {
            "status": "ok",
            "model": "eos3b5e",
            "version": "v2",
            "bucket": "myproject",
        }
        mock_persist.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                _TOOL, {"model": "eos3b5e", "bucket": "myproject", "version": "v2"}
            )
        )
        assert result.structured_content == mock_response
        mock_persist.assert_called_once_with("eos3b5e", "myproject", "v2")


def test_persist_tool_defaults_version():
    """Test the tool defaults the version to v1."""
    with patch(_PERSIST) as mock_persist:
        mock_persist.return_value = {"status": "ok"}
        asyncio.run(mcp.call_tool(_TOOL, {"model": "eos3b5e", "bucket": "myproject"}))
        mock_persist.assert_called_once_with("eos3b5e", "myproject", "v1")


def test_persist_tool_error():
    """Test the tool passes through an error status."""
    with patch(_PERSIST) as mock_persist:
        mock_persist.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool(_TOOL, {"model": "eos3b5e", "bucket": "myproject"})
        )
        assert result.structured_content["status"] == "error"
