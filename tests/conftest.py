"""Shared fixtures for the Python Maze Adventure test suite.

The UI is exercised headlessly, so SDL is forced to the dummy drivers
before pygame is imported anywhere in the tests.

Student code runs on a real worker thread, so every frame loop here sleeps
briefly in real time: the main thread and the worker thread have to take
turns, exactly as they do in the running game.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
for path in (str(GAME),):
    if path not in sys.path:
        sys.path.insert(0, path)

import pytest  # noqa: E402

from engine import constants as C  # noqa: E402
from engine.session import Session  # noqa: E402

# A single simulated clock shared by every frame loop in a test, so time
# never runs backwards between successive drive() calls.
_CLOCK = [0.0]
_FRAME = 0.05


def frame(target, seconds: float | None = None) -> None:
    """Advance one simulated frame and give the worker thread a turn."""
    target.update(_CLOCK[0])
    _CLOCK[0] += _FRAME if seconds is None else seconds
    time.sleep(0.003)


@pytest.fixture()
def session() -> Session:
    return Session()


def drive(target, code: str | None = None, answers=(), timeout: float = 15.0, start: float | None = None):
    """Run one program to completion, answering any input() prompts.

    Works for a bare Session (headless) or an App instance, because both
    expose ``session`` and ``update``.  Returns the next free simulated time.
    """
    sess = getattr(target, "session", target)
    answers = list(answers)
    if code is not None:
        sess.start_run(code)
    if start is not None:
        _CLOCK[0] = max(_CLOCK[0], start)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if sess.waiting_input is not None and answers:
            sess.submit_input(answers.pop(0))
        frame(target)
        if sess.run_state != C.RUN_RUNNING and sess.waiting_input is None:
            break
    else:  # pragma: no cover - only on a real hang
        raise AssertionError("the program did not finish in time")
    frame(target)
    return _CLOCK[0]


def pump(target, until, timeout: float = 5.0, label: str = "condition"):
    """Advance frames until ``until()`` is true, or fail loudly."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if until():
            return
        frame(target)
    raise AssertionError(f"{label} never became true")


@pytest.fixture()
def run_program():
    return drive


@pytest.fixture()
def pump_until():
    return pump
