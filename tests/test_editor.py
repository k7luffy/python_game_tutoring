"""Pure editing-model tests for the code editor (no pygame window)."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402,F401  (Document lives beside pygame imports)

from ui.editor import Document, tokenise  # noqa: E402


def make(text: str) -> Document:
    doc = Document()
    doc.set_text(text)
    return doc


def test_set_text_places_caret_at_end():
    doc = make("a\nbc")
    assert doc.lines == ["a", "bc"]
    assert (doc.row, doc.col) == (1, 2)


def test_typing_and_newline():
    doc = make("")
    doc.insert("print('hi')")
    assert doc.text == "print('hi')"
    doc.newline()
    assert doc.lines == ["print('hi')", ""]


def test_auto_indent_after_colon():
    doc = make("def go():")
    doc.end()
    doc.newline()
    assert doc.lines[1] == "    "
    doc.insert("move_one_step_right()")
    assert doc.lines[1] == "    move_one_step_right()"


def test_newline_keeps_existing_indent():
    doc = make("    if coins >= 30:")
    doc.end()
    doc.newline()
    assert doc.lines[1] == "        "


def test_backspace_soft_dedent():
    doc = make("    ")
    doc.end()
    doc.backspace()
    assert doc.lines[0] == ""


def test_backspace_at_line_start_joins_lines():
    doc = make("one\ntwo")
    doc.set_cursor(1, 0)
    doc.backspace()
    assert doc.lines == ["onetwo"]


def test_delete_at_line_end_joins_lines():
    doc = make("one\ntwo")
    doc.set_cursor(0, 3)
    doc.delete()
    assert doc.lines == ["onetwo"]


def test_selection_delete():
    doc = make("abcdef")
    doc.set_cursor(0, 1)
    doc.move(0, 3, extend=True)
    assert doc.selected_text() == "bcd"
    doc.delete_selection()
    assert doc.text == "aef"


def test_undo_and_redo():
    doc = make("start")
    doc.end()
    doc.push_undo()
    doc.insert("!")
    assert doc.text == "start!"
    doc.undo()
    assert doc.text == "start"
    doc.redo()
    assert doc.text == "start!"


def test_vertical_move_keeps_desired_column():
    doc = make("abcdef\nab\nabcdef")
    doc.set_cursor(0, 5)
    doc.move(1, 0)
    assert (doc.row, doc.col) == (1, 2)
    doc.move(1, 0)
    assert (doc.row, doc.col) == (2, 5)


def test_home_toggles_between_margin_and_first_word():
    doc = make("    hello")
    doc.end()
    doc.home()
    assert doc.col == 4
    doc.home()
    assert doc.col == 0


def test_indent_and_dedent_block():
    doc = make("one\ntwo")
    doc.set_cursor(0, 0)
    doc.select_all()
    doc.indent_block()
    assert doc.lines == ["    one", "    two"]
    doc.indent_block(dedent=True)
    assert doc.lines == ["one", "two"]


def test_tokenise_colours_code_kinds():
    kinds = {kind for _, _, kind in tokenise("coins = int(input('x'))  # note")}
    assert "keyword" not in kinds          # 'coins' is a game value
    assert "builtin" in kinds              # int
    assert "string" in kinds               # 'x'
    assert "comment" in kinds              # # note


def test_tokenise_marks_game_api_and_control_flow():
    kinds = {kind for _, _, kind in tokenise("if coins >= 30: move_one_step_right()")}
    assert "keyword" in kinds              # if
    assert "api" in kinds                  # move_one_step


def test_document_error_line_is_cleared_on_edit_activity():
    doc = make("bad line")
    doc.error_line = 0
    doc.end()
    doc.insert("x")
    assert doc.error_line is None
