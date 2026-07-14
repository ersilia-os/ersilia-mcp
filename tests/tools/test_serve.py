"""Tests for the serve_model tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_serve_model_tool_success():
    """Test the serve_model tool succeeds with model metadata."""
    with patch("ersilia_mcp.tools.serve.serve_model_helper") as mock_serve:
        mock_response = {
            "server": "pulled_docker",
            "status": "ready",
            "url": "http://localhost:5000",
        }
        mock_serve.return_value = mock_response
        result = asyncio.run(mcp.call_tool("serve_model", {"model": "eos8v1a"}))
        assert result.structured_content["result"] == mock_response
        mock_serve.assert_called_once_with("eos8v1a")


def test_serve_model_tool_failure():
    """Test the serve_model tool fails and returns empty dict."""
    with patch("ersilia_mcp.tools.serve.serve_model_helper") as mock_serve:
        mock_serve.return_value = {}
        result = asyncio.run(mcp.call_tool("serve_model", {"model": "invalid"}))
        assert result.structured_content["result"] == {}
        mock_serve.assert_called_once_with("invalid")
