"""Tests for the delete_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_delete_model_tool_success():
    """Test the delete_model tool succeeds."""
    with patch("ersilia_mcp.tools.delete.delete_model_helper") as mock_delete:
        mock_delete.return_value = {"status": "ok", "model": "eos8v1a"}
        result = asyncio.run(mcp.call_tool("delete_model", {"model": "eos8v1a"}))
        assert result.structured_content["status"] == "ok"
        mock_delete.assert_called_once_with("eos8v1a")


def test_delete_model_tool_failure():
    """Test the delete_model tool fails."""
    with patch("ersilia_mcp.tools.delete.delete_model_helper") as mock_delete:
        mock_delete.return_value = {"status": "error", "error": "not fetched"}
        result = asyncio.run(mcp.call_tool("delete_model", {"model": "invalid"}))
        assert result.structured_content["status"] == "error"
        assert result.structured_content["error"] == "not fetched"
        mock_delete.assert_called_once_with("invalid")
