"""Tests for the delete_model tool."""

import asyncio

from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_delete_model_tool_success():
    """Test the delete_model tool succeeds."""
    with patch("ersilia_mcp.tools.delete.delete_model_helper") as mock_delete:
        mock_delete.return_value = True
        result = asyncio.run(mcp.call_tool("delete_model", {"model": "eos8v1a"}))
        assert result.structured_content["result"] is True
        mock_delete.assert_called_once_with("eos8v1a")


def test_delete_model_tool_failure():
    """Test the delete_model tool fails."""
    with patch("ersilia_mcp.tools.delete.delete_model_helper") as mock_delete:
        mock_delete.return_value = False
        result = asyncio.run(mcp.call_tool("delete_model", {"model": "invalid"}))
        assert result.structured_content["result"] is False
        mock_delete.assert_called_once_with("invalid")
