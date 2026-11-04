"""Heartbeat progress for tools that run for minutes."""

import asyncio
from collections.abc import Callable
from typing import Any

from fastmcp import Context

from ersilia_mcp.utils.logging import logger

HEARTBEAT_SECONDS = 5.0


async def run_with_progress(
    ctx: Context,
    func: Callable[..., Any],
    *args: Any,
    label: str,
    interval: float = HEARTBEAT_SECONDS,
) -> Any:
    """
    Run a blocking function in a worker thread, reporting progress while it runs.

    The total work is unknown, so progress is the number of seconds elapsed.
    Each heartbeat is sent to the MCP client (clients that did not ask for
    progress ignore it) and written to the server log. A failure to report
    progress never fails the call.

    Parameters
    ----------
    ctx : fastmcp.Context
        The tool's FastMCP context, used to send progress notifications.
    func : callable
        The blocking function to run.
    *args
        Positional arguments for ``func``.
    label : str
        What is happening, e.g. ``"Fetching eos3b5e"``; used in the message.
    interval : float, default=5.0
        Seconds between heartbeats.

    Returns
    -------
    object
        Whatever ``func`` returns. Exceptions raised by ``func`` propagate.
    """
    loop = asyncio.get_running_loop()
    started = loop.time()
    future = loop.run_in_executor(None, func, *args)
    while True:
        done, _ = await asyncio.wait({future}, timeout=interval)
        if done:
            return future.result()
        elapsed = loop.time() - started
        message = f"{label} (still running, {elapsed:.0f}s elapsed)"
        logger.info(message)
        try:
            await ctx.report_progress(progress=elapsed, message=message)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Could not report progress: {exc!s}")
