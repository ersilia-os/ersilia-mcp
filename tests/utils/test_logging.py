"""Tests for MCP logging streams."""

from unittest.mock import patch

from ersilia_mcp import server


def test_startup_log_does_not_write_to_stdio_protocol(capfd):
    """The startup message belongs on stderr, not the JSON-RPC stdout."""
    with patch.object(server.mcp, "run") as run:
        server.main()

    stdout, stderr = capfd.readouterr()
    marker = "Starting Ersilia MCP server over stdio"
    assert marker not in " ".join(stdout.split())
    assert marker in " ".join(stderr.split())
    run.assert_called_once_with()
