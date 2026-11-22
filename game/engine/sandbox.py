"""Run real student Python safely, with animation-friendly pauses.

The student program runs in a worker thread.  Every game command it calls
is sent to the Pygame loop through :class:`engine.bridge.Bridge` and waits
for the animation to finish, which keeps actions in step with what the
player sees.

Safety layers:
  * AST check - no import, classes, private attributes or dangerous names.
  * Restricted builtins - no file, OS, network or import access.
  * Per-thread trace hook - line-event fuel budget, wall-clock deadline and
    a re-raising kill flag so a runaway loop is stopped.
  * Action limit - the game itself refuses more than MAX_ACTIONS commands.
"""

from __future__ import annotations

import ast
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field

from engine.bridge import Bridge, BridgeCancelled
from engine import constants as C
from education import errors
from education.errors import ErrorCard

STUDENT_FILENAME = "<student>"

BLOCKED_NAMES = {
    "eval",
    "exec",
    "open",
    "compile",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "breakpoint",
    "help",
    "exit",
    "quit",
    "__import__",
    "input_raw",
}


class ExecutionStopped(BaseException):
    """Base class for limits; BaseException so 'except Exception' won't catch it."""


class ExecutionTimeout(ExecutionStopped):
    pass


class ProgramTooLong(ExecutionStopped):
    pass


class ActionLimitExceeded(ExecutionStopped):
    pass


class ExecutionCancelled(ExecutionStopped):
    pass


@dataclass
class ConsoleLine:
    text: str
    kind: str = "student"   # student | game | ok | warn | error | system


class ConsoleBuffer:
    """Thread-safe transcript shared by the worker and the UI."""

    def __init__(self, limit: int = C.MAX_OUTPUT_LINES) -> None:
        self._lines: list[ConsoleLine] = []
        self._lock = threading.Lock()
        self.limit = limit
        self.dropped = 0

    def add(self, text: str, kind: str = "student") -> None:
        if not text:
            return
        for part in str(text).split("\n"):
            part = part[:500]
            with self._lock:
                if len(self._lines) >= self.limit:
                    self.dropped += 1
                    continue
                self._lines.append(ConsoleLine(part, kind))

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()
            self.dropped = 0

    def snapshot(self) -> list[ConsoleLine]:
        with self._lock:
            return list(self._lines)

    def __len__(self) -> int:
        with self._lock:
            return len(self._lines)


@dataclass
class RunOutcome:
    status: str                 # ok | error | cancelled | timeout | fuel | action_limit | blocked
    card: ErrorCard | None = None
    actions: int = 0
    attack_calls: int = 0
    attack_from_function: str = ""
    guard_found: bool = False
    defined_super_attack: bool = False
    super_attack_called: bool = False
    input_calls: int = 0
    input_targets: tuple[str, ...] = ()
    printed_names: tuple[str, ...] = ()
    namespace: dict = field(default_factory=dict)


def check_ast(tree: ast.AST) -> str:
    """Return a friendly reason if the tree uses something we block."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "You cannot use import in this game."
        if isinstance(node, ast.ClassDef):
            return "Classes are not needed for this mission."
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return "Private parts of objects (names starting with _) are blocked."
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            return f"'{node.id}' is not allowed in this game."
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_NAMES:
            return f"'{node.attr}' is not allowed in this game."
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_NAMES:
                return f"'{node.func.id}' is not allowed in this game."
    return ""


def _has_input_call(node: ast.AST) -> bool:
    return any(
        isinstance(sub, ast.Call)
        and isinstance(sub.func, ast.Name)
        and sub.func.id == "input"
        for sub in ast.walk(node)
    )


def source_facts(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Names stored from input() and names printed by the student.

    The Create mission uses these to check that the player really asked for a
    name and printed it, rather than passing on the game's default values.
    """
    input_targets: set[str] = set()
    printed_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _has_input_call(node.value):
            for target in node.targets:
                input_targets.update(
                    sub.id for sub in ast.walk(target) if isinstance(sub, ast.Name)
                )
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if _has_input_call(node.value):
                input_targets.update(
                    sub.id for sub in ast.walk(node.target) if isinstance(sub, ast.Name)
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            args = list(node.args) + [keyword.value for keyword in node.keywords]
            for arg in args:
                printed_names.update(
                    sub.id for sub in ast.walk(arg) if isinstance(sub, ast.Name)
                )
    return input_targets, printed_names


def _number(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if not isinstance(node.value, bool):
            return float(node.value)
    return None


def _is_coins(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "coins"


def _guards_coins(test: ast.AST) -> bool:
    """True when an if-test guarantees at least SUPER_ATTACK_COST coins."""
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    left, op = test.left, test.ops[0]
    right = test.comparators[0]
    cost = C.SUPER_ATTACK_COST
    value = _number(right)
    if _is_coins(left) and value is not None:
        if isinstance(op, ast.GtE):
            return value >= cost
        if isinstance(op, ast.Gt):
            return value >= cost - 1
        if isinstance(op, ast.Eq):
            return value >= cost
        return False
    value = _number(left)
    if _is_coins(right) and value is not None:
        if isinstance(op, ast.LtE):
            return value >= cost
        if isinstance(op, ast.Lt):
            return value >= cost - 1
        if isinstance(op, ast.Eq):
            return value >= cost
    return False


def attack_guard_lines(tree: ast.AST) -> frozenset[int]:
    """Line numbers of fire_super_attack() calls inside a coins >= 30 guard."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not _guards_coins(node.test):
            continue
        for statement in node.body:
            for sub in ast.walk(statement):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "fire_super_attack"
                ):
                    lines.add(sub.lineno)
    return frozenset(lines)


class StudentRunner:
    """One run of one student program."""

    def __init__(
        self,
        source: str,
        bridge: Bridge,
        console: ConsoleBuffer,
        *,
        extra_globals: dict | None = None,
        clock=time.monotonic,
        time_limit: float = C.TIME_LIMIT_SECONDS,
        fuel_budget: int = C.FUEL_BUDGET,
        action_limit: int = C.MAX_ACTIONS,
    ) -> None:
        self.source = source
        self.bridge = bridge
        self.console = console
        self.clock = clock
        self.time_limit = time_limit
        self.fuel_budget = fuel_budget
        self.action_limit = action_limit

        self.code = None
        self.compile_card: ErrorCard | None = None
        self.namespace: dict = dict(extra_globals or {})
        self.actions = 0
        self.attack_calls = 0
        self.attack_from_function = ""
        self.guard_lines: frozenset[int] = frozenset()
        self.super_attack_called = False
        self.input_calls = 0
        self.input_targets: set[str] = set()
        self.printed_names: set[str] = set()
        self.outcome: RunOutcome | None = None
        self.thread: threading.Thread | None = None
        self.started_at = 0.0
        self.finished_at = 0.0
        self.last_activity = 0.0

        self._ticks = 0
        self._kill: ExecutionStopped | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------ compile
    def compile(self) -> ErrorCard | None:
        if len(self.source) > C.MAX_SOURCE_CHARS:
            self.compile_card = ErrorCard(
                "Code Too Long",
                "Your program is very long. Keep it short and tidy.",
            )
            return self.compile_card
        try:
            tree = ast.parse(self.source, filename=STUDENT_FILENAME)
        except SyntaxError as exc:
            self.compile_card = errors.syntax_error_card(exc, self.source)
            return self.compile_card
        except (ValueError, MemoryError):
            self.compile_card = ErrorCard("Syntax Error", "Python could not read your code.")
            return self.compile_card
        problem = check_ast(tree)
        if problem:
            self.compile_card = errors.blocked_code_card(problem)
            return self.compile_card
        self.input_targets, self.printed_names = source_facts(tree)
        self.guard_lines = attack_guard_lines(tree)
        try:
            self.code = compile(tree, STUDENT_FILENAME, "exec", dont_inherit=True)
        except SyntaxError as exc:
            self.compile_card = errors.syntax_error_card(exc, self.source)
            return self.compile_card
        return None

    # ------------------------------------------------------------ lifecycle
    def start(self) -> None:
        if self.code is None:
            card = self.compile()
            if card is not None:
                self.outcome = RunOutcome("blocked", card)
                self.finished_at = self.clock()
                return
        self.bridge.reset()
        self.started_at = self.clock()
        self.last_activity = self.started_at
        self.thread = threading.Thread(target=self._run, name="student-code", daemon=True)
        self.thread.start()

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def stop(self) -> None:
        with self._lock:
            if self._kill is None:
                self._kill = ExecutionCancelled()
        self.bridge.cancel()

    def join(self, timeout: float = 0.0) -> bool:
        if self.thread is None:
            return True
        self.thread.join(timeout)
        return not self.thread.is_alive()

    # ------------------------------------------------------------ worker
    def _elapsed(self) -> float:
        return self.clock() - self.started_at - self.bridge.wait_seconds

    def _trace(self, frame, event, arg):
        if frame.f_code.co_filename != STUDENT_FILENAME:
            return None
        if event == "call" and frame.f_code.co_name == "super_attack":
            self.super_attack_called = True
        self._ticks += 1
        kill = self._kill
        if kill is not None:
            raise kill
        if self._ticks > self.fuel_budget:
            self._kill = ProgramTooLong()
            raise self._kill
        if self._ticks % 200 == 0 and self._elapsed() > self.time_limit:
            self._kill = ExecutionTimeout()
            raise self._kill
        return self._trace

    def _make_api(self) -> dict:
        bridge = self.bridge
        console = self.console

        def _check_kill() -> None:
            kill = self._kill
            if kill is not None:
                raise kill

        def _request(kind: str, **payload):
            _check_kill()
            self.actions += 1
            if self.actions > self.action_limit:
                self._kill = ActionLimitExceeded()
                raise self._kill
            self.last_activity = self.clock()
            try:
                result = bridge.request(kind, **payload)
            except BridgeCancelled:
                self._kill = ExecutionCancelled()
                raise self._kill from None
            if isinstance(result, dict) and "coins" in result:
                self.namespace["coins"] = result["coins"]
            return result

        def _print(*args, sep=" ", end="\n"):
            _check_kill()
            if end not in ("\n", ""):
                raise ValueError("print() here only supports end='' or a new line.")
            text = sep.join(str(arg) for arg in args) + end
            console.add(text.rstrip("\n"), "student")

        def _input(prompt=""):
            _check_kill()
            self.input_calls += 1
            text = "" if prompt is None else str(prompt)
            result = _request("input", prompt=text)
            return "" if result is None else str(result)

        def move(direction: str):
            _request("move", direction=direction)

        def move_one_step_up():
            move("up")

        def move_one_step_down():
            move("down")

        def move_one_step_left():
            move("left")

        def move_one_step_right():
            move("right")

        def fire_super_attack():
            _check_kill()
            self.attack_calls += 1
            caller = ""
            guarded = False
            try:
                frame = sys._getframe(1)
                caller = frame.f_code.co_name
                guarded = frame.f_lineno in self.guard_lines
            except Exception:
                caller = ""
                guarded = False
            if caller not in ("<module>", ""):
                self.attack_from_function = caller
            else:
                self.attack_from_function = self.attack_from_function or "<module>"
            try:
                _request("attack", guarded=guarded)
            except BridgeCancelled:
                raise ExecutionCancelled() from None

        return {
            "print": _print,
            "input": _input,
            "move_one_step_up": move_one_step_up,
            "move_one_step_down": move_one_step_down,
            "move_one_step_left": move_one_step_left,
            "move_one_step_right": move_one_step_right,
            "fire_super_attack": fire_super_attack,
        }

    def _build_namespace(self) -> dict:
        api = self._make_api()
        safe_builtins = {
            "print": api["print"],
            "input": api["input"],
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "range": range,
            "len": len,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "isinstance": isinstance,
            "Exception": Exception,
            "ValueError": ValueError,
        }
        ns = dict(self.namespace)
        ns.update(
            {
                "__builtins__": safe_builtins,
                "__name__": "__student__",
                "move_one_step_up": api["move_one_step_up"],
                "move_one_step_down": api["move_one_step_down"],
                "move_one_step_left": api["move_one_step_left"],
                "move_one_step_right": api["move_one_step_right"],
                "fire_super_attack": api["fire_super_attack"],
            }
        )
        self.namespace = ns
        return ns

    def _run(self) -> None:
        outcome = RunOutcome(status="ok")
        try:
            ns = self._build_namespace()
            sys.settrace(self._trace)
            try:
                exec(self.code, ns)  # noqa: S102 - intentionally running student code
            finally:
                sys.settrace(None)
        except ExecutionCancelled:
            outcome = RunOutcome("cancelled", errors.cancelled_card())
        except ExecutionTimeout:
            outcome = RunOutcome("timeout", errors.timeout_card(self.time_limit))
        except ProgramTooLong:
            outcome = RunOutcome("fuel", errors.fuel_card())
        except ActionLimitExceeded:
            outcome = RunOutcome("action_limit", errors.action_limit_card(self.action_limit))
        except BridgeCancelled:
            outcome = RunOutcome("cancelled", errors.cancelled_card())
        except BaseException as exc:  # student errors must never escape
            line = None
            try:
                line = errors._error_line(exc, self.source)
            except Exception:
                line = None
            card = errors.runtime_error_card(exc, self.source, line)
            outcome = RunOutcome("error", card)
        finally:
            sys.settrace(None)
            self.finished_at = self.clock()
            ns = self.namespace
            outcome.actions = self.actions
            outcome.attack_calls = self.attack_calls
            outcome.attack_from_function = self.attack_from_function
            outcome.guard_found = bool(self.guard_lines)
            outcome.defined_super_attack = callable(ns.get("super_attack"))
            outcome.super_attack_called = self.super_attack_called
            outcome.input_calls = self.input_calls
            outcome.input_targets = tuple(sorted(self.input_targets))
            outcome.printed_names = tuple(sorted(self.printed_names))
            outcome.namespace = dict(ns)
            self.outcome = outcome
