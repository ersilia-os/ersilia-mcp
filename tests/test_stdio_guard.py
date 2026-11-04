"""Tests that stray prints cannot corrupt the stdio protocol stream."""

import asyncio
import json
import select
import subprocess
import sys
import textwrap
import time

import pytest

from ersilia_mcp.utils.stdio_guard import StdoutGuard

SERVER = textwrap.dedent(
    """
    from fastmcp import FastMCP
    from ersilia_mcp.utils.stdio_guard import StdoutGuard

    mcp = FastMCP("probe")
    mcp.add_middleware(StdoutGuard())

    @mcp.tool
    def noisy() -> str:
        # Flush like Rich and click do; a buffered print would not reach the pipe.
        print("stray stdout line from a library", flush=True)
        return "ok"

    mcp.run(show_banner=False)
    """
)


def test_on_initialize_points_stdout_at_stderr(monkeypatch):
    """Test the guard redirects sys.stdout and still passes the request on."""
    monkeypatch.setattr(sys, "stdout", sys.stdout)

    async def call_next(context):
        return "handled"

    result = asyncio.run(StdoutGuard().on_initialize(None, call_next))

    assert result == "handled"
    assert sys.stdout is sys.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="uses select on pipes")
def test_stdout_stays_valid_jsonrpc_over_stdio(tmp_path):
    """Test a tool that prints to stdout does not add non-JSON lines to the stream."""
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def send(message):
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()

    lines = []
    try:
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            }
        )
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "noisy", "arguments": {}},
            }
        )
        deadline = time.time() + 30
        while time.time() < deadline:
            ready, _, _ = select.select([proc.stdout], [], [], 1)
            if not ready:
                continue
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line)
            try:
                if json.loads(line).get("id") == 2:
                    break
            except json.JSONDecodeError:
                pass
    finally:
        proc.kill()
        proc.wait()

    assert lines, "the server sent nothing"
    for line in lines:
        json.loads(line)  # raises if a stray print reached the protocol stream
    assert json.loads(lines[-1])["id"] == 2
