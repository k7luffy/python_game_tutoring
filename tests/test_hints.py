"""Progressive hints: useful, three per mission, and never the full answer."""

from __future__ import annotations

import re

import pytest

from conftest import ROOT  # noqa: F401  (ensures game/ is importable)

from engine import constants as C
from engine.session import Session
from missions import mission_one
from ui.modals import HintModal


def all_hint_sets():
    yield "create", mission_one.HINTS_CREATE
    for spec in mission_one.LEVELS:
        yield f"level{spec.number}", spec.hints
    yield "boss", mission_one.HINTS_BOSS


@pytest.mark.parametrize("name,hints", list(all_hint_sets()), ids=lambda v: v if isinstance(v, str) else "")
def test_every_mission_has_three_short_hints(name, hints):
    if not isinstance(hints, tuple):
        return
    assert len(hints) == 3, f"{name} needs exactly three hints"
    for hint in hints:
        assert hint.strip() == hint and hint, f"{name} has an empty/padded hint"
        assert len(hint) <= 160, f"{name} hint is a paragraph, not a hint: {hint!r}"
        assert "\n" not in hint, f"{name} hint should be one line"


@pytest.mark.parametrize("name,hints", list(all_hint_sets()), ids=lambda v: v if isinstance(v, str) else "")
def test_hints_never_contain_a_complete_program(name, hints):
    if not isinstance(hints, tuple):
        return
    for hint in hints:
        assert "def " not in hint, f"{name} hint defines a function: {hint!r}"
        assert "    " not in hint, f"{name} hint contains indented code: {hint!r}"
        assert hint.count("()") <= 2, f"{name} hint looks like code: {hint!r}"
        # A full route needs several moves in a row; hints may name one command.
        assert len(re.findall(r"move_one_step_\w+\(|move_right\(", hint)) <= 2


def test_create_hints_name_input_and_print():
    joined = " ".join(mission_one.HINTS_CREATE)
    assert "input(" in joined
    assert "player_name" in joined
    assert "print" in joined.lower()
    assert "int(" not in joined and "weapon_power" not in joined


def test_boss_hints_name_the_threshold_and_the_beam():
    joined = " ".join(mission_one.HINTS_BOSS)
    assert "30" in joined
    assert "fire_super_attack()" in joined
    assert "if" in joined and "else" in joined


def test_maze_hints_talk_about_their_own_budget():
    by_number = {spec.number: " ".join(spec.hints) for spec in mission_one.LEVELS}
    assert str(mission_one.LEVELS[2].start_coins) in by_number[3]
    assert "chest" in by_number[4].lower()
    assert "20" in by_number[4]
    for number, joined in by_number.items():
        assert "coin" in joined.lower(), f"level {number} hints never mention coins"


def test_session_serves_the_hints_for_the_current_mission():
    session = Session()
    assert session.current_hints() == mission_one.HINTS_CREATE
    session.select_level(3)
    assert session.current_hints() == mission_one.LEVELS[3].hints
    session.select_stage(C.STAGE_BOSS)
    assert session.current_hints() == mission_one.HINTS_BOSS


def test_hint_modal_advances_one_idea_at_a_time():
    modal = HintModal(mission_one.HINTS_BOSS, None)
    assert modal.step == 0 and modal.last is False
    assert [b.action for b in modal.buttons] == ["hint_next", "close"]
    assert modal.advance() is True
    assert modal.step == 1
    assert modal.advance() is True
    assert modal.last is True
    assert [b.action for b in modal.buttons] == ["close", "close"]
    assert modal.advance() is False


def test_only_the_final_maze_hint_offers_the_route():
    modal = HintModal(mission_one.LEVELS[0].hints, None, allow_route=True)
    assert "hint_route" not in [b.action for b in modal.buttons]
    modal.advance()
    modal.advance()
    assert modal.last
    assert "hint_route" in [b.action for b in modal.buttons]
    boss = HintModal(mission_one.HINTS_BOSS, None, start=2, allow_route=False)
    assert "hint_route" not in [b.action for b in boss.buttons], "boss has no route to show"


def test_hint_modal_reopens_on_the_saved_step():
    modal = HintModal(mission_one.LEVELS[2].hints, None, start=2)
    assert modal.step == 2 and modal.last is True
    clamped = HintModal(mission_one.LEVELS[2].hints, None, start=99)
    assert clamped.step == 2


def test_no_answer_route_appears_in_any_hint():
    for name, hints in all_hint_sets():
        if not isinstance(hints, tuple):
            continue
        blob = " ".join(hints)
        for spec in mission_one.LEVELS:
            assert spec.reference_code.splitlines()[0].strip() not in blob
        assert "for i in range(16)" not in blob
