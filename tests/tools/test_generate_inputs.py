"""Tests for the generate_inputs tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_generate_inputs_tool_success():
    """Test the generate_inputs tool returns the generation summary."""
    with patch(
        "ersilia_mcp.tools.generate_inputs.generate_inputs_helper"
    ) as mock_generate:
        mock_response = {
            "output_path": "/tmp/eos3b5e_abc.txt",
            "num_samples": 2,
            "samples": ["CCO", "CCC"],
        }
        mock_generate.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool(
                "generate_inputs",
                {"model": "eos3b5e", "n_samples": 2, "mode": "random"},
            )
        )
        assert result.structured_content == mock_response
        mock_generate.assert_called_once_with("eos3b5e", 2, "random", None)


def test_generate_inputs_tool_with_output_path():
    """Test the generate_inputs tool forwards a caller-supplied output path."""
    with patch(
        "ersilia_mcp.tools.generate_inputs.generate_inputs_helper"
    ) as mock_generate:
        mock_generate.return_value = {
            "output_path": "/data/out.txt",
            "num_samples": 1,
            "samples": ["CCO"],
        }
        asyncio.run(
            mcp.call_tool(
                "generate_inputs",
                {
                    "model": "eos3b5e",
                    "n_samples": 1,
                    "mode": "random",
                    "output_path": "/data/out.txt",
                },
            )
        )
        mock_generate.assert_called_once_with("eos3b5e", 1, "random", "/data/out.txt")


def test_generate_inputs_tool_failure():
    """Test the generate_inputs tool returns an empty dict when generation fails."""
    with patch(
        "ersilia_mcp.tools.generate_inputs.generate_inputs_helper"
    ) as mock_generate:
        mock_generate.return_value = {}
        result = asyncio.run(mcp.call_tool("generate_inputs", {"model": "invalid"}))
        assert result.structured_content == {}
        mock_generate.assert_called_once_with("invalid", 5, "random", None)
