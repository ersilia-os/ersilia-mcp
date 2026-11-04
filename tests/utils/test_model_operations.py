"""Tests for model fetching and checking."""

from unittest.mock import MagicMock, patch

from ersilia_mcp.utils.model_operations import (
    check_model_fetched_helper,
    close_model_helper,
    delete_model_helper,
    fetch_model_helper,
    serve_model_helper,
)


@patch("ersilia_mcp.utils.model_operations.Model")
def test_fetch_model_helper_already_fetched(mock_model_class):
    """Test fetch_model_helper when model is already fetched."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.return_value = True
    mock_model_class.return_value = mock_instance

    result = fetch_model_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a", "fetched": True}
    mock_instance.is_fetched.assert_called()
    mock_instance.fetch.assert_not_called()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_fetch_model_helper_not_yet_fetched(mock_model_class):
    """Test fetch_model_helper when model needs to be fetched."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.side_effect = [False, True]
    mock_model_class.return_value = mock_instance

    result = fetch_model_helper("eos8v1a")

    assert result["status"] == "ok"
    assert mock_instance.is_fetched.call_count == 2
    mock_instance.fetch.assert_called_once()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_fetch_model_helper_fetch_fails(mock_model_class):
    """Test fetch_model_helper when fetch raises an exception."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.return_value = False
    mock_instance.fetch.side_effect = Exception("Download failed")
    mock_model_class.return_value = mock_instance

    result = fetch_model_helper("eos8v1a")

    assert result == {"status": "error", "error": "Download failed"}


@patch("ersilia_mcp.utils.model_operations.Model")
def test_fetch_model_helper_not_fetched_after_fetch(mock_model_class):
    """Test fetch_model_helper reports an error if the model is still not fetched."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.return_value = False
    mock_model_class.return_value = mock_instance

    result = fetch_model_helper("eos8v1a")

    assert result["status"] == "error"
    assert "not marked as fetched" in result["error"]


@patch("ersilia_mcp.utils.model_operations.Model")
def test_check_model_fetched_helper_is_fetched(mock_model_class):
    """Test check_model_fetched_helper when model is fetched."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.return_value = True
    mock_model_class.return_value = mock_instance

    result = check_model_fetched_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a", "fetched": True}
    mock_instance.is_fetched.assert_called_once()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_check_model_fetched_helper_not_fetched(mock_model_class):
    """Test check_model_fetched_helper when model is not fetched."""
    mock_instance = MagicMock()
    mock_instance.is_fetched.return_value = False
    mock_model_class.return_value = mock_instance

    result = check_model_fetched_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a", "fetched": False}


@patch("ersilia_mcp.utils.model_operations.Model")
def test_check_model_fetched_helper_exception(mock_model_class):
    """Test check_model_fetched_helper when an exception is raised."""
    mock_model_class.side_effect = Exception("Network error")

    result = check_model_fetched_helper("eos8v1a")

    # A failed check must be distinguishable from a model that is not fetched.
    assert result == {"status": "error", "error": "Network error"}


@patch("ersilia_mcp.utils.model_operations.Model")
def test_serve_model_helper_success(mock_model_class):
    """Test serve_model_helper when serve succeeds."""
    mock_instance = MagicMock()
    mock_response = {
        "status": "ready",
        "url": "http://localhost:5000",
        "server": "pulled_docker",
    }
    mock_instance.info.return_value = mock_response
    mock_model_class.return_value = mock_instance

    result = serve_model_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a", "info": mock_response}
    mock_instance.serve.assert_called_once()
    mock_instance.info.assert_called_once()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_serve_model_helper_runtime_error(mock_model_class):
    """Test serve_model_helper when serve fails and RuntimeError is raised."""
    mock_instance = MagicMock()
    mock_instance.serve.side_effect = RuntimeError("Service unavailable")
    mock_model_class.return_value = mock_instance

    result = serve_model_helper("eos8v1a")

    assert result == {"status": "error", "error": "Service unavailable"}


@patch("ersilia_mcp.utils.model_operations.Model")
def test_serve_model_helper_system_exit(mock_model_class):
    """Test serve_model_helper contains a SystemExit instead of letting it escape."""
    mock_instance = MagicMock()
    mock_instance.serve.side_effect = SystemExit(1)
    mock_model_class.return_value = mock_instance

    result = serve_model_helper("eos8v1a")

    assert result["status"] == "error"
    assert "exited with code 1" in result["error"]


@patch("ersilia_mcp.utils.model_operations.Model")
def test_close_model_helper_success(mock_model_class):
    """Test close_model_helper when close succeeds."""
    mock_instance = MagicMock()
    mock_instance.close.return_value = True
    mock_model_class.return_value = mock_instance

    result = close_model_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a"}
    mock_instance.close.assert_called_once()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_close_model_helper_exception(mock_model_class):
    """Test close_model_helper when an exception is raised."""
    mock_model_class.side_effect = Exception("Connection error")

    result = close_model_helper("eos8v1a")

    assert result == {"status": "error", "error": "Connection error"}


@patch("ersilia_mcp.utils.model_operations.Model")
def test_delete_model_helper_success(mock_model_class):
    """Test delete_model_helper when delete succeeds."""
    mock_instance = MagicMock()
    mock_model_class.return_value = mock_instance

    result = delete_model_helper("eos8v1a")

    assert result == {"status": "ok", "model": "eos8v1a"}
    mock_instance.delete.assert_called_once()


@patch("ersilia_mcp.utils.model_operations.Model")
def test_delete_model_helper_exception(mock_model_class):
    """Test delete_model_helper when an exception is raised."""
    mock_model_class.side_effect = Exception("Deletion failed")

    result = delete_model_helper("eos8v1a")

    assert result == {"status": "error", "error": "Deletion failed"}
