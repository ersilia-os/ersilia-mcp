"""Tests for progress reporting of long-running tools."""

import asyncio
import logging
import time
from pathlib import Path

import pytest

from ersilia_mcp.utils import progress
from ersilia_mcp.utils.progress import (
    ErsiliaLogHandler,
    ProgressReporter,
    run_with_progress,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


class FakeContext:
    """Records what a tool would send to the MCP client."""

    def __init__(self, fail_progress=False, fail_info=False):
        self.reports = []
        self.infos = []
        self.fail_progress = fail_progress
        self.fail_info = fail_info

    async def report_progress(self, progress, total=None, message=None):
        if self.fail_progress:
            raise RuntimeError("client went away")
        self.reports.append((progress, total, message))

    async def info(self, message):
        if self.fail_info:
            raise RuntimeError("client went away")
        self.infos.append(message)


@pytest.fixture
def ersilia_logger():
    """Ersilia's stdlib logger at DEBUG, with the handler list restored after."""
    lg = logging.getLogger("ersilia")
    before_level, before_handlers = lg.level, list(lg.handlers)
    lg.setLevel(logging.DEBUG)
    yield lg
    lg.setLevel(before_level)
    lg.handlers[:] = before_handlers


def _slow(seconds, value="done"):
    time.sleep(seconds)
    return value


def _run(ctx, func, *args, **kwargs):
    kwargs.setdefault("label", "Fetching eos3b5e")
    kwargs.setdefault("interval", 0.1)
    return asyncio.run(run_with_progress(ctx, func, *args, **kwargs))


# --- run_with_progress ------------------------------------------------------


def test_first_report_is_immediate_even_for_a_fast_call():
    """Test a client hears about the call at once, not after the first interval."""
    ctx = FakeContext()
    assert _run(ctx, _slow, 0, "quick", interval=5.0) == "quick"
    assert len(ctx.reports) == 1
    progress_value, total, message = ctx.reports[0]
    assert total is None
    assert message.startswith("Fetching eos3b5e (")
    assert ctx.infos == []


def test_slow_call_reports_strictly_increasing_progress():
    """Test heartbeats keep coming while the work runs, always increasing."""
    ctx = FakeContext()
    assert _run(ctx, _slow, 0.45) == "done"
    values = [p for p, _, _ in ctx.reports]
    assert len(values) >= 3
    assert all(b > a for a, b in zip(values, values[1:]))
    assert all(total is None for _, total, _ in ctx.reports)


def test_ersilia_log_lines_become_stage_messages_and_log_notifications(
    ersilia_logger,
):
    """Test what Ersilia logs while a call runs shows up as the current stage."""

    def work():
        ersilia_logger.info("Model doesn't exist on your system, fetching it now.")
        time.sleep(0.3)
        ersilia_logger.debug("Checking that container works")
        time.sleep(0.3)
        return "done"

    ctx = FakeContext()
    assert _run(ctx, work) == "done"

    messages = [m for _, _, m in ctx.reports]
    assert any("fetching it now" in m for m in messages)
    assert any("Checking that container works" in m for m in messages)
    # One MCP log message per distinct stage, as a fallback for clients that
    # do not display progress notifications.
    assert len(ctx.infos) == 2
    assert "fetching it now" in ctx.infos[0]


def test_docker_layer_count_appears_in_the_message(ersilia_logger):
    """Test layer events are summarised as n/m layers, not echoed line by line."""
    lines = (FIXTURES / "docker_pull_nontty.txt").read_text().splitlines()

    def work():
        for line in lines[:8]:  # the pull header, 4 announcements, 3 progress lines
            ersilia_logger.info(line)
        time.sleep(0.3)
        return "done"

    ctx = FakeContext()
    _run(ctx, work)

    messages = [m for _, _, m in ctx.reports]
    assert any(
        m.startswith("Fetching eos3b5e: Downloading image layers — 0/4 layers (")
        for m in messages
    ), messages
    # Raw docker lines are not forwarded one by one.
    assert not any("Pulling fs layer" in m for m in messages)


def test_countable_progress_is_determinate_and_still_increasing():
    """Test on_progress gives done/total, and a stalled count is nudged upward."""

    def work(on_progress):
        on_progress(1000, 2500, "1000/2500 inputs")
        time.sleep(0.45)  # a long chunk: heartbeats must still increase
        on_progress(2500, 2500, "2500/2500 inputs")
        return "done"

    ctx = FakeContext()
    assert _run(ctx, work, with_reporter=True) == "done"

    determinate = [(p, t, m) for p, t, m in ctx.reports if t == 2500]
    assert determinate
    assert determinate[0][0] == 1000
    assert "1000/2500 inputs" in determinate[0][2]
    values = [p for p, _, _ in ctx.reports]
    assert all(b > a for a, b in zip(values, values[1:]))
    assert any(1000 < p < 1001 for p, _, _ in determinate)  # nudged heartbeat


def test_final_count_is_sent_before_the_result_returns():
    """Test a call that finishes between updates still reports its last state."""

    def work(on_progress):
        on_progress(2500, 2500, "2500/2500 inputs")  # then returns immediately
        return "done"

    ctx = FakeContext()
    assert _run(ctx, work, with_reporter=True, interval=5.0) == "done"

    progress_value, total, message = ctx.reports[-1]
    assert (progress_value, total) == (2500, 2500)
    assert "2500/2500 inputs" in message


def test_no_final_update_when_the_call_failed_or_nothing_changed():
    """Test an extra update is only sent for a successful call whose state changed."""
    ctx = FakeContext()
    _run(ctx, _slow, 0, interval=5.0)
    assert len(ctx.reports) == 1  # just the immediate first report


def test_client_errors_never_fail_the_call():
    """Test a client that cannot receive progress does not break the tool."""
    ctx = FakeContext(fail_progress=True, fail_info=True)
    assert _run(ctx, _slow, 0.25) == "done"


def test_exception_from_function_propagates_and_handler_is_removed(ersilia_logger):
    """Test errors are not swallowed, and nothing is left on Ersilia's logger."""
    before = list(ersilia_logger.handlers)

    def boom():
        raise ValueError("bad model")

    with pytest.raises(ValueError, match="bad model"):
        _run(FakeContext(), boom)

    assert ersilia_logger.handlers == before
    assert progress._listener is None


def test_only_one_call_listens_to_ersilia_at_a_time(ersilia_logger):
    """Test a second concurrent call falls back to heartbeats only."""
    first = progress._attach_log_handler(ProgressReporter("a"))
    try:
        assert first is not None
        assert progress._attach_log_handler(ProgressReporter("b")) is None
    finally:
        progress._detach_log_handler(first)
    again = progress._attach_log_handler(ProgressReporter("c"))
    assert again is not None
    progress._detach_log_handler(again)


# --- ErsiliaLogHandler ------------------------------------------------------


def _feed(lines, ersilia_logger, level=logging.INFO):
    reporter = ProgressReporter("Fetching eos3b5e")
    handler = ErsiliaLogHandler(reporter)
    ersilia_logger.addHandler(handler)
    try:
        for line in lines:
            ersilia_logger.log(level, line)
    finally:
        ersilia_logger.removeHandler(handler)
    return reporter


def test_real_docker_pull_output_is_counted_by_layer(ersilia_logger):
    """Test the captured non-TTY docker pull output yields 4/4 layers."""
    lines = (FIXTURES / "docker_pull_nontty.txt").read_text().splitlines()
    first_digest = next(i for i, ln in enumerate(lines) if ln.startswith("Digest:"))

    # Only the "Pulling fs layer" announcements: 0 of 4 done.
    announced = _feed(lines[:5], ersilia_logger).snapshot()
    assert announced.stage == "Downloading image layers"
    assert "0/4 layers" in announced.message

    # Every layer line: 4 of 4 done.
    pulled = _feed(lines[:first_digest], ersilia_logger).snapshot()
    assert "4/4 layers" in pulled.message

    # The closing "Digest"/"Status" lines become the stage text.
    finished = _feed(lines, ersilia_logger).snapshot()
    assert finished.stage == "docker.io/library/python:3.12-alpine"


def test_already_exists_counts_as_a_finished_layer(ersilia_logger):
    """Test cached layers count as done, like Ersilia's own progress bar."""
    snap = _feed(
        ["aaaaaaaaaaaa: Already exists", "bbbbbbbbbbbb: Pulling fs layer"],
        ersilia_logger,
    ).snapshot()
    assert "1/2 layers" in snap.message


@pytest.mark.parametrize(
    "line",
    [
        "Pulling image ersiliaos/eos3b5e:latest from DockerHub...",
        "latest: Pulling from ersiliaos/eos3b5e",  # docker's own header line
    ],
)
def test_pull_announcements_are_shortened(ersilia_logger, line):
    """Test both pull announcements become the same plain stage."""
    assert _feed([line], ersilia_logger).snapshot().stage == (
        "Pulling image from DockerHub"
    )


def test_noise_is_ignored_and_text_is_cleaned(ersilia_logger):
    """Test errors, blanks and dumps are skipped; terminal codes are stripped."""
    reporter = _feed([""], ersilia_logger)
    assert reporter.snapshot().stage is None

    assert (
        _feed(["something failed"], ersilia_logger, logging.ERROR).snapshot().stage
        is None
    )
    assert _feed(["x" * 400], ersilia_logger).snapshot().stage is None

    snap = _feed(
        ["\x1b[32m  Writing   model\tsource \x1b[0m"], ersilia_logger
    ).snapshot()
    assert snap.stage == "Writing model source"

    long = _feed(["word " * 40], ersilia_logger).snapshot().stage
    assert len(long) == 120 and long.endswith("…")


def test_repeated_stage_does_not_count_as_a_change(ersilia_logger):
    """Test the same message twice is one stage, so one log notification."""
    reporter = _feed(
        ["Fetching from DockerHub", "Fetching from DockerHub"], ersilia_logger
    )
    assert reporter.snapshot().stage_seq == 1


def test_handler_never_raises_into_ersilia_logging(ersilia_logger):
    """Test a broken reporter cannot break Ersilia's own logging."""

    class Broken:
        def stage(self, text):
            raise RuntimeError("boom")

        detail = stage

    handler = ErsiliaLogHandler(Broken())
    ersilia_logger.addHandler(handler)
    try:
        ersilia_logger.info("anything")  # must not raise
    finally:
        ersilia_logger.removeHandler(handler)
