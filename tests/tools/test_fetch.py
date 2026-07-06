"""Tests for the fetch_model and check_model_fetched tools."""

import asyncio

from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_fetch_model_tool_success():
    """Test the fetch_model tool succeeds."""
    with patch("ersilia_mcp.tools.fetch.fetch_model_helper") as mock_fetch:
        mock_fetch.return_value = True
        result = asyncio.run(mcp.call_tool("fetch_model", {"model": "eos8v1a"}))
        assert result.structured_content["result"] is True
        mock_fetch.assert_called_once_with("eos8v1a")


def test_fetch_model_tool_failure():
    """Test the fetch_model tool fails."""
    with patch("ersilia_mcp.tools.fetch.fetch_model_helper") as mock_fetch:
        mock_fetch.return_value = False
        result = asyncio.run(mcp.call_tool("fetch_model", {"model": "invalid"}))
        assert result.structured_content["result"] is False
        mock_fetch.assert_called_once_with("invalid")


def test_check_model_fetched_tool_true():
    """Test the check_model_fetched tool returns True."""
    with patch("ersilia_mcp.tools.fetch.check_model_fetched_helper") as mock_check:
        mock_check.return_value = True
        result = asyncio.run(mcp.call_tool("check_model_fetched", {"model": "eos8v1a"}))
        assert result.structured_content["result"] is True
        mock_check.assert_called_once_with("eos8v1a")


def test_check_model_fetched_tool_false():
    """Test the check_model_fetched tool returns False."""
    with patch("ersilia_mcp.tools.fetch.check_model_fetched_helper") as mock_check:
        mock_check.return_value = False
        result = asyncio.run(
            mcp.call_tool("check_model_fetched", {"model": "notfetched"})
        )
        assert result.structured_content["result"] is False
        mock_check.assert_called_once_with("notfetched")
