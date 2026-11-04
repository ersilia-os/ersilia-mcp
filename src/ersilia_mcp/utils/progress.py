"""Progress reporting for tools that run for minutes.

A blocking helper runs in a worker thread. While it runs, two things feed a
small thread-safe :class:`ProgressReporter`: the helper itself (for work it can
count, such as predicting in chunks) and a log handler attached to Ersilia's
logger (for what Ersilia says it is doing, e.g. which Docker layers are
downloaded). A single async loop in :func:`run_with_progress` is the only code
that talks to the MCP client, so notifications stay in order and none is sent
after the tool has returned.
"""

import asyncio
import functools
import logging
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastmcp import Context

from ersilia_mcp.utils.logging import logger

HEARTBEAT_SECONDS = 5.0
MAX_MESSAGE_CHARS = 120
MAX_RECORD_CHARS = 300  # longer records are dumps, not status lines

_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
# One line per Docker layer event, e.g. "d3531b7a4f21: Pull complete". Same
# pattern Ersilia uses for its own progress bar.
_DOCKER_LAYER = re.compile(r"^([a-f0-9]{12,}): (.+)$")
_LAYER_DONE = ("Pull complete", "Already exists")
# Ersilia's own announcement, and docker's "<tag>: Pulling from <repo>" header.
_PULLING_IMAGE = re.compile(r"^(Pulling image .+ from DockerHub|\S+: Pulling from \S+)")


@dataclass(frozen=True)
class Snapshot:
    """A consistent view of the progress state at one moment."""

    version: int
    stage_seq: int
    stage: str | None
    value: float
    total: float | None
    message: str


class ProgressReporter:
    """
    Thread-safe holder of what a long-running operation is doing right now.

    Worker threads and log handlers call :meth:`stage`, :meth:`detail` and
    :meth:`progress`; the async sender reads :meth:`snapshot`.

    Parameters
    ----------
    label : str
        What is happening overall, e.g. ``"Fetching eos3b5e"``.
    """

    def __init__(self, label: str) -> None:
        self.label = label
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._stage: str | None = None
        self._detail: str | None = None
        self._done: float | None = None
        self._total: float | None = None
        self._version = 0
        self._stage_seq = 0

    def stage(self, text: str) -> None:
        """
        Set the current stage (e.g. ``"Downloading image layers"``).

        A new stage clears the previous detail and counts as a stage change,
        which the sender also announces as an MCP log message.
        """
        with self._lock:
            if text == self._stage:
                return
            self._stage = text
            self._detail = None
            self._stage_seq += 1
            self._version += 1

    def detail(self, text: str) -> None:
        """Set a short detail for the current stage (e.g. ``"3/7 layers"``)."""
        with self._lock:
            if text == self._detail:
                return
            self._detail = text
            self._version += 1

    def progress(
        self, done: float, total: float | None = None, message: str | None = None
    ) -> None:
        """
        Record countable progress, which makes the MCP progress determinate.

        Parameters
        ----------
        done : float
            Units of work completed so far.
        total : float, optional
            Total units of work, if known.
        message : str, optional
            Short detail to show, e.g. ``"3000/12000 inputs"``.
        """
        with self._lock:
            self._done = done
            self._total = total
            if message is not None:
                self._detail = message
            self._version += 1

    def snapshot(self) -> Snapshot:
        """Return the current state, with the message already composed."""
        with self._lock:
            elapsed = time.monotonic() - self._started
            body = " — ".join(p for p in (self._stage, self._detail) if p)
            head = f"{self.label}: {body}" if body else self.label
            return Snapshot(
                version=self._version,
                stage_seq=self._stage_seq,
                stage=self._stage,
                value=self._done if self._done is not None else elapsed,
                total=self._total if self._done is not None else None,
                message=f"{head} ({elapsed:.0f} s)",
            )


def _clean(text: str) -> str:
    """Strip terminal codes, collapse whitespace and cap the length."""
    text = " ".join(_ANSI.sub("", text).split())
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 1] + "…"
    return text


class ErsiliaLogHandler(logging.Handler):
    """
    Turn Ersilia's own log records into progress state.

    Docker layer lines (``<id>: Pulling fs layer`` ... ``Pull complete``) become
    a ``n/m layers`` count. Any other INFO or DEBUG record becomes the current
    stage text. Errors are ignored here: the tool's result already carries them.

    Parameters
    ----------
    reporter : ProgressReporter
        Where to record what Ersilia reports.
    """

    def __init__(self, reporter: ProgressReporter) -> None:
        super().__init__(level=logging.DEBUG)
        self._reporter = reporter
        self._seen: set[str] = set()
        self._done: set[str] = set()

    def emit(self, record: logging.LogRecord) -> None:
        """Update the reporter from one log record; never raise into the logger."""
        try:
            if record.levelno >= logging.ERROR:
                return
            raw = record.getMessage()
            if not raw.strip() or len(raw) > MAX_RECORD_CHARS:
                return
            text = _clean(raw)
            layer = _DOCKER_LAYER.match(text)
            if layer:
                self._seen.add(layer.group(1))
                if layer.group(2).strip() in _LAYER_DONE:
                    self._done.add(layer.group(1))
                self._reporter.stage("Downloading image layers")
                self._reporter.detail(f"{len(self._done)}/{len(self._seen)} layers")
            elif _PULLING_IMAGE.match(text):
                self._reporter.stage("Pulling image from DockerHub")
            else:
                self._reporter.stage(text)
        except Exception:  # noqa: BLE001
            pass  # a progress bug must never break Ersilia's logging


# Ersilia keeps global state, so only one tracked call listens to its logger at
# a time; a second concurrent call falls back to heartbeats only.
_listener_lock = threading.Lock()
_listener: ErsiliaLogHandler | None = None


def _attach_log_handler(reporter: ProgressReporter) -> ErsiliaLogHandler | None:
    """Attach a handler to Ersilia's logger unless another call already did."""
    global _listener
    with _listener_lock:
        if _listener is not None:
            return None
        _listener = ErsiliaLogHandler(reporter)
        logging.getLogger("ersilia").addHandler(_listener)
        return _listener


def _detach_log_handler(handler: ErsiliaLogHandler | None) -> None:
    """Remove ``handler`` from Ersilia's logger and free the listener slot."""
    global _listener
    if handler is None:
        return
    with _listener_lock:
        logging.getLogger("ersilia").removeHandler(handler)
        _listener = None


async def _send(ctx: Context, snap: Snapshot, value: float, announce: bool) -> None:
    """Send one progress notification (and a log message on a stage change)."""
    try:
        await ctx.report_progress(
            progress=value, total=snap.total, message=snap.message
        )
        if announce and snap.stage:
            await ctx.info(snap.message)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Could not report progress: {exc!s}")


async def run_with_progress(
    ctx: Context,
    func: Callable[..., Any],
    *args: Any,
    label: str,
    interval: float = HEARTBEAT_SECONDS,
    with_reporter: bool = False,
) -> Any:
    """
    Run a blocking function in a worker thread and report progress while it runs.

    Progress is the elapsed seconds, with the current stage and detail in the
    message, unless the function reports countable work (see ``with_reporter``),
    in which case it is that count out of its total. The value always strictly
    increases, as the MCP specification requires. Clients that did not ask for
    progress ignore the notifications; stage changes are also sent as MCP log
    messages and written to the server log. A failure to report never fails the
    call.

    Parameters
    ----------
    ctx : fastmcp.Context
        The tool's FastMCP context, used to send notifications.
    func : callable
        The blocking function to run.
    *args
        Positional arguments for ``func``.
    label : str
        What is happening overall, e.g. ``"Fetching eos3b5e"``.
    interval : float, default=5.0
        Seconds between heartbeats when nothing else changed. Changes are sent
        sooner, at most once per ``min(interval, 1)`` seconds.
    with_reporter : bool, default=False
        If true, call ``func(*args, on_progress=...)`` where ``on_progress`` is
        ``ProgressReporter.progress(done, total, message)``.

    Returns
    -------
    object
        Whatever ``func`` returns. Exceptions raised by ``func`` propagate.
    """
    loop = asyncio.get_running_loop()
    reporter = ProgressReporter(label)
    kwargs = {"on_progress": reporter.progress} if with_reporter else {}
    handler = _attach_log_handler(reporter)
    tick = min(1.0, interval)
    last_value = -1.0
    last_sent = float("-inf")
    sent_version = -1
    announced_stage = 0

    async def send(*, force: bool) -> None:
        nonlocal last_value, last_sent, sent_version, announced_stage
        snap = reporter.snapshot()
        now = loop.time()
        changed = snap.version != sent_version
        due = now - last_sent >= interval
        if not (force or due or (changed and now - last_sent >= tick)):
            return
        value = snap.value if snap.value > last_value else last_value + 1e-3
        announce = snap.stage_seq != announced_stage
        if announce and snap.stage:
            logger.info(snap.message)
        last_value, last_sent = value, now
        sent_version, announced_stage = snap.version, snap.stage_seq
        await _send(ctx, snap, value, announce)

    try:
        await send(force=True)
        future = loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
        while True:
            done, _ = await asyncio.wait({future}, timeout=tick)
            if done:
                return future.result()
            await send(force=False)
    finally:
        _detach_log_handler(handler)
