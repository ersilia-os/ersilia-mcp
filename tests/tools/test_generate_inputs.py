"""Tests for the generate_inputs tool."""

import asyncio
from unittest.mock import patch

from ersilia_mcp.server import mcp


def test_generate_inputs_tool_success():
    """Test the generate_inputs tool returns the generated samples."""
    with patch(
        "ersilia_mcp.tools.generate_inputs.generate_inputs_helper"
    ) as mock_generate:
        mock_generate.return_value = ["CCO", "CCC"]
        result = asyncio.run(
            mcp.call_tool(
                "generate_inputs",
                {"model": "eos3b5e", "n_samples": 2, "mode": "random"},
            )
        )
        assert result.structured_content["result"] == ["CCO", "CCC"]
        mock_generate.assert_called_once_with("eos3b5e", 2, "random")


def test_generate_inputs_tool_failure():
    """Test the generate_inputs tool returns an empty list when generation fails."""
    with patch(
        "ersilia_mcp.tools.generate_inputs.generate_inputs_helper"
    ) as mock_generate:
        mock_generate.return_value = []
        result = asyncio.run(mcp.call_tool("generate_inputs", {"model": "invalid"}))
        assert result.structured_content["result"] == []
        mock_generate.assert_called_once_with("invalid", 5, "random")
