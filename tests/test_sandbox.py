"""Sandbox safety tests: what runs, what is blocked, and what stops it."""

from __future__ import annotations

import time

import pytest

from engine import constants as C
from engine.bridge import Bridge
from engine.sandbox import (
    ConsoleBuffer,
    StudentRunner,
    attack_guard_lines,
    check_ast,
    ActionLimitExceeded,
)

import ast


def make_runner(source: str, **kwargs) -> StudentRunner:
    kwargs.setdefault("fuel_budget", 20_000)
    kwargs.setdefault("time_limit", 5.0)
    return StudentRunner(source, Bridge(), ConsoleBuffer(), **kwargs)


def run_to_end(runner: StudentRunner, timeout: float = 8.0) -> None:
    runner.start()
    assert runner.join(timeout), "worker did not stop"


def test_blocks_import():
    tree = ast.parse("import os\n")
    assert "import" in check_ast(tree).lower()


def test_blocks_classes():
    tree = ast.parse("class Thing:\n    pass\n")
    assert "class" in check_ast(tree).lower()


def test_blocks_private_attributes():
    tree = ast.parse("x = (1).__class__\n")
    assert "_" in check_ast(tree)


def test_blocks_eval_open_exec():
    for source in ("eval('1+1')\n", "open('x')\n", "exec('x=1')\n"):
        runner = make_runner(source)
        card = runner.compile()
        assert card is not None, source
        assert card.title == "Not Allowed"


def test_syntax_error_card_points_at_line():
    runner = make_runner("def broken(:\n    pass\n")
    card = runner.compile()
    assert card is not None
    assert card.title == "Syntax Error"
    assert card.line_number == 1


def test_restricted_builtins_do_not_exist():
    runner = make_runner("open('file.txt')\n")
    assert runner.compile() is not None  # blocked before it runs

    runner = make_runner("result = __import__('os')\n")
    assert runner.compile() is not None


def test_infinite_loop_hits_fuel_budget():
    runner = make_runner("while True:\n    pass\n", fuel_budget=5_000)
    run_to_end(runner)
    assert runner.outcome is not None
    assert runner.outcome.status in ("fuel", "timeout")
    assert runner.outcome.card is not None


def test_bare_except_cannot_swallow_the_stop():
    source = "try:\n    while True:\n        pass\nexcept Exception:\n    pass\n"
    runner = make_runner(source, fuel_budget=5_000)
    run_to_end(runner)
    assert runner.outcome.status in ("fuel", "timeout")


def test_print_and_input_are_captured():
    runner = make_runner("print('hello')\nname = input('Who? ')\nprint('hi', name)\n")
    assert runner.compile() is None

    # Stand in for the UI: answer the input request from a helper thread.
    import threading

    def answer():
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            request = runner.bridge.poll()
            if request is not None:
                runner.bridge.respond(request, "Ada")
                return
            time.sleep(0.001)

    thread = threading.Thread(target=answer, daemon=True)
    thread.start()
    run_to_end(runner)
    lines = [line.text for line in runner.console.snapshot()]
    assert "hello" in lines
    assert "hi Ada" in lines
    assert runner.outcome.status == "ok"


def test_action_limit_counts_directional_moves():
    source = "for i in range(500):\n    move_one_step_right()\n"
    runner = make_runner(source)
    runner.action_limit = 10

    import threading

    def answer():
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            request = runner.bridge.poll()
            if request is not None:
                runner.bridge.respond(request, {"coins": 50})
            elif runner.outcome is not None:
                return
            time.sleep(0.0005)

    thread = threading.Thread(target=answer, daemon=True)
    thread.start()
    run_to_end(runner)
    assert runner.outcome.status == "action_limit"
    assert runner.outcome.card.title == "Too Many Moves"


def test_result_namespace_reports_defined_function():
    runner = make_runner("def super_attack():\n    pass\n\nsuper_attack()\n")
    run_to_end(runner)
    assert runner.outcome.defined_super_attack is True
    assert runner.outcome.super_attack_called is True


def test_namespace_has_four_moves_and_no_turn_commands():
    namespace = make_runner("")._build_namespace()
    for name in (
        "move_one_step_up",
        "move_one_step_down",
        "move_one_step_left",
        "move_one_step_right",
        "fire_super_attack",
    ):
        assert callable(namespace[name]), name
    assert "move_one_step" not in namespace
    assert "turn_left" not in namespace
    assert "turn_right" not in namespace


def _guard_lines(source: str) -> frozenset[int]:
    return attack_guard_lines(ast.parse(source))


def test_guard_accepts_at_least_thirty():
    for condition in (
        "coins >= 30", "30 <= coins", "coins > 29", "29 < coins", "coins == 30", "coins > 30",
    ):
        source = (
            "def super_attack():\n"
            f"    if {condition}:\n"
            "        fire_super_attack()\n\n"
            "super_attack()\n"
        )
        assert _guard_lines(source), condition


def test_guard_rejects_weaker_or_unguarded_checks():
    for condition in ("coins >= 29", "coins != 30", "coins", "True"):
        source = (
            "def super_attack():\n"
            f"    if {condition}:\n"
            "        fire_super_attack()\n\n"
            "super_attack()\n"
        )
        assert not _guard_lines(source), condition
    source = (
        "def super_attack():\n"
        "    fire_super_attack()\n\n"
        "super_attack()\n"
    )
    assert not _guard_lines(source)
    outside = (
        "if coins >= 30:\n"
        "    print('ready')\n"
        "fire_super_attack()\n"
    )
    assert not _guard_lines(outside)


def test_guard_accepts_nested_statements_inside_the_if():
    source = (
        "def super_attack():\n"
        "    if coins >= 30:\n"
        "        print('charging')\n"
        "        if player_name:\n"
        "            fire_super_attack()\n\n"
        "super_attack()\n"
    )
    assert _guard_lines(source)


def test_outcome_records_whether_a_guard_exists():
    guarded = make_runner(
        "def super_attack():\n"
        "    if coins >= 30:\n"
        "        fire_super_attack()\n"
    )
    run_to_end(guarded)
    assert guarded.outcome.guard_found is True

    unguarded = make_runner(
        "def super_attack():\n"
        "    fire_super_attack()\n"
    )
    run_to_end(unguarded)
    assert unguarded.outcome.guard_found is False
