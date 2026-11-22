"""Thread-safe request/response bridge between student code and the game.

Student code runs on a worker thread.  Game functions such as
``move_one_step_right()`` call :meth:`Bridge.request`, which puts a request on a
queue and then blocks until the Pygame loop has animated the action and
answered.  The bridge keeps the two threads in step without ever blocking
the game loop.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field


class BridgeCancelled(BaseException):
    """Raised inside the worker thread when a run has been cancelled."""


CANCELLED = object()


@dataclass
class Request:
    rid: int
    kind: str
    payload: dict
    event: threading.Event = field(default_factory=threading.Event)
    result: object = None
    answered: bool = False


class Bridge:
    """A one-at-a-time request queue with per-request events."""

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._queue: queue.Queue[Request] = queue.Queue()
        self._lock = threading.Lock()
        self._next_id = 1
        self._cancelled = False
        self.wait_seconds = 0.0

    # ------------------------------------------------------------ lifecycle
    def reset(self) -> None:
        """Prepare for a new run (must not be used while a run is live)."""
        self.cancel()
        with self._lock:
            self._cancelled = False
            self.wait_seconds = 0.0
        self._drain()

    def cancel(self) -> None:
        """Cancel the run: unblock the worker and drop queued requests."""
        with self._lock:
            self._cancelled = True
        self._drain()

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def _drain(self) -> None:
        while True:
            try:
                request = self._queue.get_nowait()
            except queue.Empty:
                return
            self._answer(request, CANCELLED)

    # ------------------------------------------------------------ worker side
    def request(self, kind: str, **payload) -> object:
        """Called from the worker thread; blocks until the UI responds."""
        if self.cancelled:
            raise BridgeCancelled()
        with self._lock:
            rid = self._next_id
            self._next_id += 1
        request = Request(rid=rid, kind=kind, payload=payload)
        self._queue.put(request)
        started = self._clock()
        try:
            while not request.event.wait(0.03):
                if self.cancelled:
                    raise BridgeCancelled()
        finally:
            self.wait_seconds += self._clock() - started
        if self.cancelled or request.result is CANCELLED:
            raise BridgeCancelled()
        return request.result

    # ------------------------------------------------------------ UI side
    def poll(self) -> Request | None:
        """Return the next pending request without blocking."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def respond(self, request: Request, result) -> None:
        self._answer(request, result)

    def _answer(self, request: Request, result) -> None:
        with self._lock:
            if request.answered:
                return
            request.answered = True
        request.result = result
        request.event.set()
