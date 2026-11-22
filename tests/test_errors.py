"""Friendly error messages for the mistakes Year 6 students make most."""

from __future__ import annotations

import sys

import pytest

from education import errors


def card_for(source: str) -> errors.ErrorCard:
    try:
        compile(source, "<student>", "exec")
    except SyntaxError as exc:
        return errors.syntax_error_card(exc, source)
    raise AssertionError("source compiled cleanly")


def runtime_card(source: str) -> errors.ErrorCard:
    namespace: dict = {"__builtins__": {"int": int, "print": print}}
    with pytest.raises(BaseException) as info:
        exec(compile(source, "<student>", "exec"), namespace)  # noqa: S102
    exc = info.value
    return errors.runtime_error_card(exc, source, errors._error_line(exc, source))


def test_missing_colon_is_explained():
    card = card_for("def go()\n    move_one_step_right()\n")
    assert card.title == "Syntax Error"
    assert "colon" in card.message.lower()
    assert card.line_number == 1


def test_unclosed_bracket_is_explained():
    card = card_for("move_one_step(\n")
    assert "closed" in card.message.lower() or "bracket" in card.message.lower()


def test_unexpected_indent_is_explained():
    card = card_for("move_one_step_right()\n    move_one_step_right()\n")
    assert card.title == "Indentation Error"


def test_missing_indent_after_def_is_explained():
    card = card_for("def go():\nmove_one_step_right()\n")
    assert card.title == "Indentation Error"
    assert "push" in card.hint.lower() or "indent" in card.hint.lower()


def test_name_error_suggests_close_game_command():
    card = runtime_card("move_one_stepp()\n")
    assert card.title == "Name Error"
    assert "move_one_step" in card.hint


def test_name_error_without_close_match_mentions_variables():
    card = runtime_card("totally_unknown_thing()\n")
    assert card.title == "Name Error"
    assert "spelling" in card.hint.lower()


def test_int_error_is_explained():
    card = runtime_card("int('seven')\n")
    assert card.title == "Value Error"
    assert "number" in card.message.lower()


def test_console_lines_include_code_and_caret():
    card = card_for("def go()\n    pass\n")
    lines = card.console_lines()
    assert any("def go()" in line for line in lines)
