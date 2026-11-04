"""Tests for the structured error helpers."""

from ersilia_mcp.utils.errors import error_message, error_result


def test_error_message_ordinary_exception():
    """Test an ordinary exception is reported by its message."""
    assert error_message(RuntimeError("boom")) == "boom"


def test_error_message_empty_exception_falls_back_to_class_name():
    """Test an exception with no message is still informative."""
    assert error_message(KeyError()) == "KeyError"


def test_error_message_system_exit_points_to_log():
    """Test SystemExit is not reported as a bare exit code."""
    message = error_message(SystemExit(1))
    assert "exited with code 1" in message
    assert "~/eos/mcp/logs" in message


def test_error_result_from_string_and_exception():
    """Test error_result accepts either a message or an exception."""
    assert error_result("bad") == {"status": "error", "error": "bad"}
    assert error_result(ValueError("worse")) == {"status": "error", "error": "worse"}
