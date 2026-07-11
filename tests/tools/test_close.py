"""Tests for the close_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_close_model_tool_success():
    """Test the close_model tool succeeds."""
    with patch("ersilia_mcp.tools.close.close_model_helper") as mock_close:
        mock_close.return_value = True
        result = asyncio.run(mcp.call_tool("close_model", {"model": "eos8v1a"}))
        assert result.structured_content["result"] is True
        mock_close.assert_called_once_with("eos8v1a")


def test_close_model_tool_failure():
    """Test the close_model tool fails and returns False."""
    with patch("ersilia_mcp.tools.close.close_model_helper") as mock_close:
        mock_close.return_value = False
        result = asyncio.run(mcp.call_tool("close_model", {"model": "invalid"}))
        assert result.structured_content["result"] is False
        mock_close.assert_called_once_with("invalid")
