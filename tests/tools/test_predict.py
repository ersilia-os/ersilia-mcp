"""Tests for the predict tool."""

import asyncio
from unittest.mock import ANY, patch

from ersilia_mcp.server import mcp


def test_predict_tool_success():
    """Test the predict tool returns the prediction summary."""
    with patch("ersilia_mcp.tools.predict.predict_helper") as mock_predict:
        mock_response = {
            "status": "ok",
            "output_path": "/tmp/eos3b5e_abc.csv",
            "num_predictions": 2,
            "columns": ["input", "value"],
        }
        mock_predict.return_value = mock_response
        result = asyncio.run(
            mcp.call_tool("predict", {"model": "eos3b5e", "input_data": "CCO,CCC"})
        )
        assert result.structured_content == mock_response
        mock_predict.assert_called_once_with(
            "eos3b5e", "CCO,CCC", None, on_progress=ANY
        )


def test_predict_tool_with_output_path():
    """Test the predict tool forwards a caller-supplied output path."""
    with patch("ersilia_mcp.tools.predict.predict_helper") as mock_predict:
        mock_predict.return_value = {
            "status": "ok",
            "output_path": "/data/out.csv",
            "num_predictions": 1,
            "columns": ["input", "value"],
        }
        asyncio.run(
            mcp.call_tool(
                "predict",
                {
                    "model": "eos3b5e",
                    "input_data": "CCO",
                    "output_path": "/data/out.csv",
                },
            )
        )
        mock_predict.assert_called_once_with(
            "eos3b5e", "CCO", "/data/out.csv", on_progress=ANY
        )


def test_predict_tool_failure():
    """Test the predict tool surfaces the error message when prediction fails."""
    with patch("ersilia_mcp.tools.predict.predict_helper") as mock_predict:
        mock_predict.return_value = {"status": "error", "error": "Model crashed"}
        result = asyncio.run(
            mcp.call_tool("predict", {"model": "invalid", "input_data": "CCO"})
        )
        assert result.structured_content == {
            "status": "error",
            "error": "Model crashed",
        }
        mock_predict.assert_called_once_with("invalid", "CCO", None, on_progress=ANY)
