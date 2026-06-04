"""Smoke tests exercising the MCP server's tool and resource in-memory."""

import asyncio

from ersilia_mcp.server import mcp


def test_hello_tool():
    # call_tool returns (content_blocks, structured_result); the tool's
    # return value lands in the structured result under "result".
    _, structured = asyncio.run(mcp.call_tool("hello", {"name": "Ersilia"}))
    assert structured["result"] == "Hello, Ersilia!"


def test_greeting_resource():
    contents = asyncio.run(mcp.read_resource("greeting://hello"))
    assert "Hello" in next(iter(contents)).content
