"""Headless UI tests: the whole window is built and rendered through pygame."""

from __future__ import annotations

import pygame
import pytest

from conftest import drive, pump

import main
from education.starter_code import COMMANDS_BY_STAGE, EDITOR_PLACEHOLDER
from engine import constants as C
from missions import mission_one
from ui.modals import HintModal, NoticeModal


@pytest.fixture()
def app():
    application = main.App()
    yield application
    pygame.quit()


def test_canvas_and_layout(app):
    assert app.canvas.get_size() == (C.WINDOW_WIDTH, C.WINDOW_HEIGHT)
    assert set(app.buttons) >= {
        "run", "reset", "stage1", "stage2", "stage3", "help", "sound", "hint",
        "level1", "level2", "level3", "level4",
    }
    assert "level5" not in app.buttons


def test_editors_start_empty_with_a_placeholder(app):
    assert app.doc.text == ""
    assert app.editor.placeholder == EDITOR_PLACEHOLDER[1]
    app.switch_level(0)
    assert app.doc.text == ""
    assert "route" in app.editor.placeholder.lower()
    app.switch_stage(3)
    assert app.doc.text == ""
    assert "super_attack" in app.editor.placeholder.lower()


def test_command_strip_covers_every_stage():
    assert set(COMMANDS_BY_STAGE) == {1, 2, 3}
    maze = " ".join(code for code, _ in COMMANDS_BY_STAGE[2])
    for name in (
        "move_one_step_up()",
        "move_one_step_down()",
        "move_one_step_left()",
        "move_one_step_right()",
    ):
        assert name in maze, name
    assert "turn_" not in maze and "move_one_step()" not in maze
    boss = " ".join(code for code, _ in COMMANDS_BY_STAGE[3])
    assert "fire_super_attack()" in boss
    assert all(name in boss for name in (
        "move_one_step_up()", "move_one_step_down()",
        "move_one_step_left()", "move_one_step_right()",
    ))


def test_every_stage_and_level_draws(app, tmp_path):
    for stage in (1, 2, 3):
        app.switch_stage(stage, force=True)
        app.update(1.0)
        app.draw(1.0)
        pygame.image.save(app.canvas, str(tmp_path / f"stage{stage}.png"))
    for index in range(len(mission_one.LEVELS)):
        app.switch_level(index)
        app.update(1.0)
        app.draw(1.0)
        pygame.image.save(app.canvas, str(tmp_path / f"level{index + 1}.png"))
    assert app.canvas.get_at((10, 10)) != (0, 0, 0)
    assert (tmp_path / "level4.png").exists()
    assert not (tmp_path / "level5.png").exists()


def test_run_button_turns_into_stop(app):
    app.switch_stage(2, force=True)
    app.doc.set_text("move_one_step_right()\nmove_one_step_right()\n")
    app.handle_action("run")
    app.update(0.1)
    assert app.buttons["run"].label == "Stop"
    app.handle_action("run")
    app.update(0.2)
    assert app.buttons["run"].label == "Run Code"


def test_input_modal_answers_reach_the_program(app):
    app.switch_stage(1, force=True)
    app.doc.set_text(
        "player_name = input('Name? ')\n"
        "print('Welcome', player_name)\n"
    )
    app.handle_action("run")
    pump(app, lambda: app.modal is not None, label="the input prompt")
    assert app.modal.__class__.__name__ == "InputModal"
    for ch in "Nova":
        app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=ch))
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    drive(app, timeout=10.0)
    assert app.session.player_name == "Nova"
    assert app.session.weapon_power == C.DEFAULT_WEAPON_POWER
    assert app.session.has_character is True


def test_speed_button_cycles(app):
    before = app.buttons["speed"].label
    app.handle_action("speed")
    assert app.buttons["speed"].label != before
    app.handle_action("speed")
    app.handle_action("speed")
    assert app.buttons["speed"].label == before


def test_hint_modal_walks_through_and_reveals_the_route(app):
    app.switch_level(3)
    app.handle_action("hint")
    assert isinstance(app.modal, HintModal)
    assert app.modal.step == 0
    assert not app.show_route
    app.modal_action("hint_next")
    app.modal_action("hint_next")
    assert app.modal.step == 2 and app.modal.last
    assert any(button.action == "hint_route" for button in app.modal.buttons)
    app.draw(1.0)
    app.modal_action("hint_route")
    assert app.modal is None
    assert app.show_route is True
    path = app.arena.route()
    assert path[-1] == app.session.maze.base
    assert len(path) - 1 == mission_one.LEVELS[3].expected_steps


def test_boss_hint_has_no_route_reveal(app):
    app.switch_stage(3)
    app.handle_action("hint")
    app.modal_action("hint_next")
    app.modal_action("hint_next")
    assert app.modal.last
    assert not any(button.action == "hint_route" for button in app.modal.buttons)


def test_level_dot_click_switches_level(app):
    app.switch_stage(2, force=True)
    app.draw(0.5)
    rect = app.buttons["level3"].rect
    window_pos = (
        int(rect.centerx * app.scale + app.offset[0]),
        int(rect.centery * app.scale + app.offset[1]),
    )
    app.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=window_pos)
    )
    assert app.session.level_index == 2
    assert app.stage == C.STAGE_MAZE


def test_help_modal_opens_and_closes(app):
    app.handle_action("help")
    assert app.modal is not None and app.modal.__class__.__name__ == "HelpModal"
    app.draw(1.0)
    action = app.modal.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert action == "close"


def test_reset_restores_the_current_level(app):
    app.switch_level(3)
    app.doc.set_text("move_one_step_right()\n")
    app.handle_action("run")
    drive(app, timeout=10.0)
    assert app.session.coins == mission_one.LEVELS[3].start_coins - 1
    app.handle_action("reset")
    assert app.session.coins == mission_one.LEVELS[3].start_coins
    assert app.session.steps == 0


def test_next_level_notice_advances_and_resets_the_view(app):
    app.switch_level(0)
    app.doc.set_text(mission_one.LEVELS[0].reference_code)
    app.handle_action("run")
    drive(app, timeout=15.0)
    assert isinstance(app.modal, NoticeModal)
    assert app.modal.primary_action == "next_level"
    app.modal_action("next_level")
    assert app.session.level_index == 1
    assert app.session.coins == mission_one.LEVELS[1].start_coins
    assert app.doc.text == mission_one.LEVELS[0].reference_code


def test_full_campaign_golden(app):
    """Create the explorer, clear all four levels, then defeat the boss."""
    app.session.speed_index = 2
    app.switch_stage(1, force=True)
    app.doc.set_text(
        "player_name = input('Name? ')\nprint('Welcome', player_name)\n"
    )
    app.handle_action("run")
    drive(app, answers=["Nova"], timeout=10.0)
    assert app.session.has_character is True
    app.modal_action("next")

    for index, spec in enumerate(mission_one.LEVELS):
        app.switch_level(index)
        app.doc.set_text(spec.reference_code)
        app.handle_action("run")
        drive(app, timeout=25.0)
        assert app.session.reached_base is True
        if index < len(mission_one.LEVELS) - 1:
            assert app.modal.primary_action == "next_level"
            app.modal_action("next_level")
        else:
            app.modal_action("next")

    assert app.session.maze_done is True
    assert app.stage == C.STAGE_BOSS
    app.doc.set_text(mission_one.BOSS_ANSWER)
    app.handle_action("run")
    drive(app, timeout=20.0)
    assert app.session.boss_defeated is True
    assert app.session.boss_done is True
    assert app.session.progress_label() == "3 of 3 missions complete"


def test_boss_hp_bar_clears_the_hint_button(app):
    app.switch_stage(3, force=True)
    app.draw(0.5)
    bar = app.boss_bar_rect
    hint = app.buttons["hint"].rect
    assert bar.right <= hint.left, "the boss bar must not sit under the Hint button"
