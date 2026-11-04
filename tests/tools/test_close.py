"""Tests for the close_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_close_model_tool_success():
    """Test the close_model tool succeeds."""
    with patch("ersilia_mcp.tools.close.close_model_helper") as mock_close:
        mock_close.return_value = {"status": "ok", "model": "eos8v1a"}
        result = asyncio.run(mcp.call_tool("close_model", {"model": "eos8v1a"}))
        assert result.structured_content["status"] == "ok"
        mock_close.assert_called_once_with("eos8v1a")


def test_close_model_tool_failure():
    """Test the close_model tool surfaces the error message."""
    with patch("ersilia_mcp.tools.close.close_model_helper") as mock_close:
        mock_close.return_value = {"status": "error", "error": "not served"}
        result = asyncio.run(mcp.call_tool("close_model", {"model": "invalid"}))
        assert result.structured_content["status"] == "error"
        assert result.structured_content["error"] == "not served"
        mock_close.assert_called_once_with("invalid")
