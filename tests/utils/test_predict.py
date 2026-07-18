"""Tests for input parsing and prediction helpers."""

import os
from unittest.mock import MagicMock, patch

import pandas as pd

from ersilia_mcp.utils.predict import parse_input, predict_helper


def test_parse_input_from_string_commas_and_newlines():
    """Test that a delimited string is split on commas and newlines."""
    result = parse_input("CCO,CCC\nCCCC")
    assert result == ["CCO", "CCC", "CCCC"]


def test_parse_input_strips_whitespace_and_drops_empties():
    """Test that whitespace is stripped and empty entries removed."""
    result = parse_input(" CCO , , \n  CCC \n")
    assert result == ["CCO", "CCC"]


def test_parse_input_from_file(tmp_path):
    """Test that inputs are read line-by-line from an existing file."""
    input_file = tmp_path / "inputs.txt"
    input_file.write_text("CCO\nCCC\n\nCCCC\n")
    result = parse_input(str(input_file))
    assert result == ["CCO", "CCC", "CCCC"]


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_success(mock_model_class, tmp_path):
    """Test predict_helper runs the model and writes results to CSV."""
    mock_instance = MagicMock()
    mock_instance.run.return_value = pd.DataFrame(
        {"input": ["CCO", "CCC"], "value": [1.0, 2.0]}
    )
    mock_model_class.return_value = mock_instance

    output_path = tmp_path / "out.csv"
    result = predict_helper("eos3b5e", "CCO,CCC", str(output_path))

    assert result == {
        "output_path": str(output_path),
        "num_predictions": 2,
        "columns": ["input", "value"],
    }
    mock_instance.run.assert_called_once_with(["CCO", "CCC"])
    assert output_path.exists()


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_default_output_path(mock_model_class):
    """Test predict_helper creates a temp CSV when no output path is given."""
    mock_instance = MagicMock()
    mock_instance.run.return_value = pd.DataFrame({"input": ["CCO"], "value": [1.0]})
    mock_model_class.return_value = mock_instance

    result = predict_helper("eos3b5e", "CCO")

    try:
        assert result["num_predictions"] == 1
        assert result["output_path"].endswith(".csv")
    finally:
        os.remove(result["output_path"])


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_no_valid_inputs(mock_model_class):
    """Test predict_helper returns an empty dict when there are no inputs."""
    result = predict_helper("eos3b5e", "  ,  \n ")

    assert result == {}
    mock_model_class.assert_not_called()


@patch("ersilia_mcp.utils.predict.Model")
def test_predict_helper_run_fails(mock_model_class):
    """Test predict_helper returns an empty dict when the model run errors."""
    mock_instance = MagicMock()
    mock_instance.run.side_effect = Exception("Model crashed")
    mock_model_class.return_value = mock_instance

    result = predict_helper("eos3b5e", "CCO")

    assert result == {}
