"""Tests for the example input generation helper."""

from unittest.mock import MagicMock, patch

from ersilia_mcp.utils.generate_inputs import generate_inputs_helper


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_success(mock_model_class):
    """Test generate_inputs_helper returns the samples from the model."""
    mock_instance = MagicMock()
    mock_instance.example.return_value = ["CCO", "CCC", "CCCC"]
    mock_model_class.return_value = mock_instance

    result = generate_inputs_helper("eos3b5e", n_samples=3, mode="deterministic")

    assert result == ["CCO", "CCC", "CCCC"]
    mock_instance.example.assert_called_once_with(n_samples=3, mode="deterministic")


@patch("ersilia_mcp.utils.generate_inputs.Model")
def test_generate_inputs_helper_error(mock_model_class):
    """Test generate_inputs_helper returns an empty list when the model is not served."""
    mock_instance = MagicMock()
    mock_instance.example.side_effect = Exception("Model not served")
    mock_model_class.return_value = mock_instance

    result = generate_inputs_helper("eos3b5e")

    assert result == []
