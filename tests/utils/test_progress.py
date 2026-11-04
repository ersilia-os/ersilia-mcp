"""Tests for the heartbeat progress helper."""

import asyncio
import time

import pytest

from ersilia_mcp.utils.progress import run_with_progress


class FakeContext:
    """Records the progress reports a tool would send to the client."""

    def __init__(self, fail=False):
        self.reports = []
        self.fail = fail

    async def report_progress(self, progress, total=None, message=None):
        if self.fail:
            raise RuntimeError("client went away")
        self.reports.append((progress, total, message))


def _slow(seconds, value="done"):
    time.sleep(seconds)
    return value


def test_slow_call_reports_increasing_progress_and_returns_result():
    """Test heartbeats are sent while the function runs, then its result returned."""
    ctx = FakeContext()
    result = asyncio.run(
        run_with_progress(ctx, _slow, 0.35, label="Fetching eos3b5e", interval=0.1)
    )

    assert result == "done"
    assert len(ctx.reports) >= 2
    progress = [p for p, _, _ in ctx.reports]
    assert progress == sorted(progress) and len(set(progress)) == len(progress)
    assert all(total is None for _, total, _ in ctx.reports)
    assert all(m.startswith("Fetching eos3b5e (still running") for *_, m in ctx.reports)


def test_fast_call_reports_nothing():
    """Test a call that finishes before the first heartbeat sends no progress."""
    ctx = FakeContext()
    result = asyncio.run(
        run_with_progress(ctx, _slow, 0, "quick", label="x", interval=5.0)
    )

    assert result == "quick"
    assert ctx.reports == []


def test_exception_from_function_propagates():
    """Test an error raised by the blocking function is not swallowed."""

    def boom():
        raise ValueError("bad model")

    with pytest.raises(ValueError, match="bad model"):
        asyncio.run(run_with_progress(FakeContext(), boom, label="x", interval=0.1))


def test_progress_failure_does_not_fail_the_call():
    """Test a client that cannot receive progress does not break the tool."""
    result = asyncio.run(
        run_with_progress(FakeContext(fail=True), _slow, 0.25, label="x", interval=0.1)
    )

    assert result == "done"
