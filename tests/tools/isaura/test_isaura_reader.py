"""Tests for the read_precalculations_from_isaura tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp

_READ = "ersilia_mcp.utils.isaura.isaura_operations.read"
_TOOL = "read_precalculations_from_isaura"


def test_read_precalculations_tool_success():
    """Test the tool returns the read summary and forwards every argument."""
    with patch(_READ) as mock_read:
        mock_response = {
            "status": "ok",
            "num_requested": 2,
            "num_cached": 2,
            "num_missing": 0,
            "output_path": "/tmp/eos3b5e_abc.csv",
            "columns": ["input", "value"],
        }
        mock_read.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                _TOOL,
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
            "eos3b5e", "CCO,CCC", "v2", "isaura-private", "/data/out.csv", False
        )


def test_read_precalculations_tool_defaults_to_not_verbose():
    """Test the tool omits the missing list unless verbose is requested."""
    with patch(_READ) as mock_read:
        mock_read.return_value = {
            "status": "ok",
            "num_requested": 2,
            "num_cached": 1,
            "num_missing": 1,
            "output_path": "/tmp/eos3b5e_abc.csv",
            "columns": ["input", "value"],
        }
        result = asyncio.run(
            mcp.call_tool(_TOOL, {"model": "eos3b5e", "input_data": "CCO,CCC"})
        )
        assert "missing" not in result.structured_content
        mock_read.assert_called_once_with(
            "eos3b5e", "CCO,CCC", "v1", "isaura-public", None, False
        )


def test_read_precalculations_tool_verbose_returns_missing():
    """Test the tool passes verbose through and surfaces the missing inputs."""
    with patch(_READ) as mock_read:
        mock_read.return_value = {
            "status": "ok",
            "num_requested": 2,
            "num_cached": 1,
            "num_missing": 1,
            "output_path": "/tmp/eos3b5e_abc.csv",
            "columns": ["input", "value"],
            "missing": ["CCC"],
        }
        result = asyncio.run(
            mcp.call_tool(
                _TOOL,
                {"model": "eos3b5e", "input_data": "CCO,CCC", "verbose": True},
            )
        )
        assert result.structured_content["missing"] == ["CCC"]
        mock_read.assert_called_once_with(
            "eos3b5e", "CCO,CCC", "v1", "isaura-public", None, True
        )


def test_read_precalculations_tool_error():
    """Test the tool passes through an error status."""
    with patch(_READ) as mock_read:
        mock_read.return_value = {"status": "error", "error": "store unreachable"}
        result = asyncio.run(
            mcp.call_tool(_TOOL, {"model": "eos3b5e", "input_data": "CCO"})
        )
        assert result.structured_content["status"] == "error"
