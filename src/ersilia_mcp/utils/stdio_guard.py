"""Keep stray prints from corrupting the MCP stdio protocol stream."""

import sys

from fastmcp.server.middleware import Middleware


class StdoutGuard(Middleware):
    """
    Send Python-level writes to ``sys.stdout`` to stderr once the server is up.

    Over stdio, stdout carries the JSON-RPC messages, so any other write to it
    (Ersilia's console logs, ``echo`` output or progress bars) corrupts the
    stream. The transport captures the real stdout buffer when it starts, before
    the first ``initialize`` request arrives, so pointing ``sys.stdout`` at
    stderr from here on does not affect the protocol messages.

    Only writes made through ``sys.stdout`` are redirected. Child processes
    that inherit file descriptor 1 are not.
    """

    async def on_initialize(self, context, call_next):
        """Redirect ``sys.stdout`` to stderr, then handle the request as usual."""
        sys.stdout = sys.stderr
        return await call_next(context)
