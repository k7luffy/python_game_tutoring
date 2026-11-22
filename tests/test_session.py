"""Game-rule tests: four-level flow, coins, checkpoints and the finale."""

from __future__ import annotations

import pytest

from conftest import drive

from engine import constants as C
from missions import mission_one

WINNER = mission_one.BOSS_ANSWER

DRAIN_L4 = """\
for i in range(34):
    move_one_step_right()
    move_one_step_left()
"""

LEVELS = mission_one.LEVELS


def console_text(session) -> str:
    return "\n".join(line.text for line in session.console.snapshot())


def play_level(session, index: int) -> None:
    session.select_level(index)
    session.start_run(LEVELS[index].reference_code)
    drive(session, timeout=25.0)


def test_every_move_costs_one_coin(session):
    session.select_level(0)
    session.start_run("move_one_step_right()\n")
    drive(session)
    assert session.steps == 1
    assert session.coins == LEVELS[0].start_coins - 1


def test_wall_blocks_without_charging(session):
    session.select_level(0)
    session.start_run("move_one_step_up()\n")   # the wall is directly above the start
    drive(session)
    assert session.coins == LEVELS[0].start_coins
    assert session.steps == 0
    assert (session.player.x, session.player.y) == session.maze.start
    assert "BONK" in console_text(session)


def test_coin_value_is_fresh_inside_the_program(session):
    session.select_level(0)
    session.start_run("move_one_step_right()\nprint('coins now', coins)\n")
    drive(session)
    assert f"coins now {LEVELS[0].start_coins - 1}" in console_text(session)


@pytest.mark.parametrize("index", range(len(LEVELS)), ids=lambda i: f"L{i + 1}")
def test_each_reference_route_finishes_its_level(session, index):
    spec = LEVELS[index]
    play_level(session, index)
    assert session.reached_base is True
    assert session.steps == spec.expected_steps
    assert session.levels_done == {index}
    assert session.notice is not None and session.notice.kind == "success"
    if index < len(LEVELS) - 1:
        assert session.maze_done is False
        assert session.coins == spec.expected_coins
        assert session.checkpoint_coins == 0
        assert session.notice.action == "next_level"
    else:
        assert session.maze_done is True
        assert session.coins == C.FINAL_BONUS_TARGET
        assert session.checkpoint_coins == C.FINAL_BONUS_TARGET
        assert session.notice.action == "next_stage"


def test_next_level_keeps_the_campaign_moving(session):
    session.select_stage(C.STAGE_MAZE)
    for index, spec in enumerate(LEVELS):
        assert session.level_index == index
        assert session.coins == spec.start_coins
        session.start_run(spec.reference_code)
        drive(session, timeout=25.0)
        assert session.reached_base is True
        if index < len(LEVELS) - 1:
            assert session.advance_level() is True
    assert session.advance_level() is False
    assert session.maze_done is True
    assert session.coins == C.FINAL_BONUS_TARGET


def test_levels_start_with_their_own_coins(session):
    for index, spec in enumerate(LEVELS):
        session.select_level(index)
        assert session.coins == spec.start_coins
        assert session.maze is session.levels[index]
        assert session.stage == C.STAGE_MAZE


def test_running_out_of_coins_fails_the_mission(session):
    session.select_level(3)                      # level 4 starts with 33 coins
    session.start_run(DRAIN_L4)
    drive(session, timeout=25.0)
    assert session.coins == 0
    assert session.mission_failed is True
    assert session.notice is not None
    assert "coins" in session.notice.title.lower()
    assert session.coins >= 0


def test_early_levels_do_not_write_the_boss_checkpoint(session):
    play_level(session, 0)
    assert session.coins == LEVELS[0].expected_coins
    assert session.levels_done == {0}
    assert session.checkpoint_coins == 0
    assert session.maze_done is False


def test_final_level_tops_up_to_fifty(session):
    play_level(session, len(LEVELS) - 1)
    assert session.coins == 50
    assert session.checkpoint_coins == 50
    assert "bonus" in console_text(session).lower()


def test_create_stage_needs_input_and_a_printed_name(session):
    session.select_stage(C.STAGE_CREATE)
    session.start_run(
        "player_name = input('Name? ')\n"
        "print('Welcome', player_name)\n"
    )
    drive(session, answers=["Nova"])
    assert session.has_character is True
    assert session.player_name == "Nova"
    assert session.weapon_power == C.DEFAULT_WEAPON_POWER
    assert session.notice.kind == "success"
    assert any("30" in line for line in session.notice.lines)


def test_create_stage_rejects_a_name_that_was_not_typed(session):
    session.select_stage(C.STAGE_CREATE)
    session.start_run("player_name = 'Nova'\nprint(player_name)\n")
    drive(session)
    assert session.has_character is False
    assert session.notice.kind == "info"
    assert any("input()" in line for line in session.notice.lines)


def test_create_stage_rejects_an_unprinted_name(session):
    session.select_stage(C.STAGE_CREATE)
    session.start_run("player_name = input('Name? ')\n")
    drive(session, answers=["Nova"])
    assert session.has_character is False
    assert session.notice.kind == "info"
    assert any("print" in line.lower() for line in session.notice.lines)


def test_create_stage_ignores_a_blank_program(session):
    session.select_stage(C.STAGE_CREATE)
    session.start_run("")
    drive(session)
    assert session.has_character is False
    assert session.notice.kind == "info"


def test_create_stage_fixes_weapon_power_at_five(session):
    session.select_stage(C.STAGE_CREATE)
    session.start_run(
        "player_name = input('Name? ')\n"
        "weapon_power = 9\n"
        "print(player_name)\n"
    )
    drive(session, answers=["Nova"])
    assert session.has_character is True
    assert session.weapon_power == C.DEFAULT_WEAPON_POWER == 5


def test_boss_uses_the_checkpoint_after_the_campaign(session):
    play_level(session, len(LEVELS) - 1)
    session.select_stage(C.STAGE_BOSS)
    assert session.coins == 50
    assert session.practice_run is False
    assert (session.player.x, session.player.y) == session.boss_maze.start == (1, 1)
    assert session.player.facing == 1


def test_boss_practice_run_uses_fifty(session):
    session.select_stage(C.STAGE_BOSS)
    assert session.coins == C.PRACTICE_COINS == 50
    assert session.practice_run is True
    assert (session.player.x, session.player.y) == (1, 1)


def test_boss_is_defeated_with_enough_coins(session):
    play_level(session, len(LEVELS) - 1)
    session.select_stage(C.STAGE_BOSS)
    session.start_run(WINNER)
    drive(session, timeout=25.0)
    assert session.boss_defeated is True
    assert session.boss_done is True
    assert session.boss_hp == 0
    assert session.notice.kind == "success"
    assert session.score() == session.coins * 2 + session.weapon_power * 10


def test_boss_fizzles_when_coins_are_low(session):
    session.player_name = "Nova"
    session.maze_done = True
    session.checkpoint_coins = 35           # 20-step walk leaves only 15
    session.select_stage(C.STAGE_BOSS)
    session.start_run(WINNER)
    drive(session, timeout=25.0)
    assert session.boss_defeated is False
    assert session.boss_done is False
    assert session.notice is not None
    assert "not enough coins" in session.notice.title.lower()


def test_boss_survives_when_function_is_never_called(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(WINNER.replace("\nsuper_attack()\n", "\n"))
    drive(session)
    assert session.boss_defeated is False
    assert session.notice is not None
    assert "still standing" in session.notice.title.lower()


def test_super_attack_without_fire_command_is_explained(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(
        mission_one.BOSS_ROUTE_CODE
        + "def super_attack():\n"
        "    if coins >= 30:\n"
        "        print('Super Attack Activated!')\n"
        "super_attack()\n"
    )
    drive(session, timeout=25.0)
    assert session.boss_defeated is False
    assert "fire_super_attack" in "\n".join(session.notice.lines)


def test_boss_walk_reaches_the_pad_with_thirty_coins(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(mission_one.BOSS_ROUTE_CODE)
    drive(session, timeout=25.0)
    assert session.reached_goal is True
    assert (session.player.x, session.player.y) == session.boss_maze.goal == (17, 5)
    assert session.coins == 30
    assert session.notice.kind == "info"
    assert session.reached_goal is True


def test_boss_tile_is_blocked(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(
        mission_one.BOSS_ROUTE_CODE
        + "move_one_step_down()\nmove_one_step_down()\n"
    )
    drive(session, timeout=25.0)
    assert (session.player.x, session.player.y) == (17, 6)
    assert session.coins == 29
    assert "boss blocks" in console_text(session).lower()


def test_boss_requires_the_attack_pad(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(
        "def super_attack():\n"
        "    if coins >= 30:\n"
        "        fire_super_attack()\n\n"
        "super_attack()\n"
    )
    drive(session)
    assert session.boss_defeated is False
    assert session.attack_off_pad is True
    assert session.notice.title == "Fire from the attack pad"
    assert "attack pad" in "\n".join(session.notice.lines).lower()


def test_boss_requires_the_coin_guard(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(
        mission_one.BOSS_ROUTE_CODE
        + "def super_attack():\n"
        "    fire_super_attack()\n\n"
        "super_attack()\n"
    )
    drive(session, timeout=25.0)
    assert session.boss_defeated is False
    assert session.attack_unguarded is True
    assert session.notice.title == "Add the coin check"
    assert "coins >= 30" in "\n".join(session.notice.lines)


def test_boss_accepts_a_reversed_coin_guard(session):
    session.select_stage(C.STAGE_BOSS)
    session.start_run(
        mission_one.BOSS_ROUTE_CODE
        + "def super_attack():\n"
        "    if 30 <= coins:\n"
        "        fire_super_attack()\n\n"
        "super_attack()\n"
    )
    drive(session, timeout=25.0)
    assert session.boss_defeated is True


def test_reset_stage_restores_the_current_level(session):
    session.select_level(3)
    session.start_run("move_one_step_right()\n")
    drive(session)
    assert session.coins == LEVELS[3].start_coins - 1
    session.reset_stage()
    assert session.coins == LEVELS[3].start_coins
    assert session.steps == 0
    assert (session.player.x, session.player.y) == session.maze.start
    assert session.boss_hp == 100


def test_reset_all_clears_the_campaign(session):
    play_level(session, len(LEVELS) - 1)
    assert session.maze_done is True
    session.reset_all()
    assert session.maze_done is False
    assert session.boss_done is False
    assert session.has_character is False
    assert session.level_index == 0
    assert session.levels_done == set()
    assert session.checkpoint_coins == 0
    assert session.stage == C.STAGE_CREATE
    assert session.coins == LEVELS[0].start_coins


def test_hints_and_objectives_follow_the_stage(session):
    assert len(session.current_hints()) == 3
    assert session.current_objective() == mission_one.OBJECTIVE_CREATE
    session.select_level(2)
    assert session.current_hints() == LEVELS[2].hints
    assert session.current_objective() == LEVELS[2].objective
    assert "Level 3 of 4" in session.level_label()
    session.select_stage(C.STAGE_BOSS)
    assert session.current_hints() == mission_one.HINTS_BOSS
    assert session.current_objective() == mission_one.OBJECTIVE_BOSS


def test_reference_path_matches_the_teacher_route(session):
    for index, spec in enumerate(LEVELS):
        session.select_level(index)
        path = session.current_reference_path()
        assert path is not None
        assert path[-1] == session.maze.base
        assert len(path) - 1 == spec.expected_steps
