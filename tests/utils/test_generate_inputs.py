"""Tests for the example input generation helper."""

import os
from unittest.mock import MagicMock, patch

from ersilia_mcp.utils.generate_inputs import generate_inputs_helper


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_success(mock_model_class, tmp_path):
    """Test generate_inputs_helper writes all samples to a file and returns a summary."""
    mock_instance = MagicMock()
    mock_instance.example.return_value = ["CCO", "CCC", "CCCC"]
    mock_model_class.return_value = mock_instance

    output_path = tmp_path / "out.txt"
    result = generate_inputs_helper(
        "eos3b5e", n_samples=3, mode="deterministic", output_path=str(output_path)
    )

    assert result == {
        "output_path": str(output_path),
        "num_samples": 3,
        "samples": ["CCO", "CCC", "CCCC"],
    }
    mock_instance.example.assert_called_once_with(n_samples=3, mode="deterministic")
    assert output_path.read_text() == "CCO\nCCC\nCCCC\n"


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_caps_preview(mock_model_class, tmp_path):
    """Test the returned preview is capped at 20 samples while the file has all of them."""
    samples = [f"C{i}" for i in range(25)]
    mock_instance = MagicMock()
    mock_instance.example.return_value = samples
    mock_model_class.return_value = mock_instance

    output_path = tmp_path / "out.txt"
    result = generate_inputs_helper(
        "eos3b5e", n_samples=25, output_path=str(output_path)
    )

    assert result["num_samples"] == 25
    assert result["samples"] == samples[:20]
    assert output_path.read_text().splitlines() == samples


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_default_output_path(mock_model_class):
    """Test generate_inputs_helper creates a temp file when no output path is given."""
    mock_instance = MagicMock()
    mock_instance.example.return_value = ["CCO"]
    mock_model_class.return_value = mock_instance

    result = generate_inputs_helper("eos3b5e", n_samples=1)

    try:
        assert result["num_samples"] == 1
        assert result["output_path"].endswith(".txt")
    finally:
        os.remove(result["output_path"])


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_no_samples(mock_model_class):
    """Test generate_inputs_helper returns an empty dict when no samples are generated."""
    mock_instance = MagicMock()
    mock_instance.example.return_value = []
    mock_model_class.return_value = mock_instance

    result = generate_inputs_helper("eos3b5e")

    assert result == {}


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_error(mock_model_class):
    """Test generate_inputs_helper returns an empty dict when the model is not served."""
    mock_instance = MagicMock()
    mock_instance.example.side_effect = Exception("Model not served")
    mock_model_class.return_value = mock_instance

    result = generate_inputs_helper("eos3b5e")

    assert result == {}
