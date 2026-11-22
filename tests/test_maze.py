"""Maze layout, connectivity, reference-route and coin-economy tests."""

from __future__ import annotations

import pytest

from engine import constants as C
from engine.maze import Maze, MazeError
from missions import mission_one

SPECS = mission_one.LEVELS


@pytest.fixture(params=SPECS, ids=lambda spec: f"L{spec.number}")
def spec(request):
    return request.param


@pytest.fixture()
def maze(spec) -> Maze:
    return Maze.from_ascii(spec.maze_ascii)


def _height(ascii_map: str) -> int:
    return len([row for row in ascii_map.splitlines() if row])


def test_dimensions_and_endpoints(maze, spec):
    assert maze.width == 19
    assert maze.height == _height(spec.maze_ascii)
    assert maze.is_walkable(*maze.start)
    assert maze.is_walkable(*maze.base)
    assert maze.start != maze.base


def test_supplies_are_normalised(maze):
    for supply in maze.supplies:
        assert maze.is_walkable(supply.x, supply.y)
        assert supply.kind in {"coin", "chest"}
        assert supply.value == (C.COIN_VALUE if supply.kind == "coin" else C.CHEST_VALUE)


def test_shortest_path_is_connected_and_ends_at_base(maze, spec):
    path = maze.shortest_path()
    assert path[0] == maze.start
    assert path[-1] == maze.base
    assert len(path) - 1 == maze.shortest_steps() == spec.shortest_steps
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        assert abs(ax - bx) + abs(ay - by) == 1
        assert maze.is_walkable(bx, by)


def test_every_supply_is_reachable(maze):
    distances = maze.distances_from(maze.start)
    for supply in maze.supplies:
        assert (supply.x, supply.y) in distances


def test_shortest_route_economy_matches_the_table(maze, spec):
    path = maze.shortest_path()
    steps = len(path) - 1
    coins = spec.start_coins - steps + maze.supplies_on_path(path)
    assert coins == spec.direct_coins


def test_reference_route_is_the_teacher_answer(maze, spec):
    cells = mission_one.reference_path(maze, spec)
    assert cells[0] == maze.start
    assert cells[-1] == maze.base
    assert len(cells) - 1 == spec.expected_steps
    steps = len(cells) - 1
    supplies = {(supply.x, supply.y) for supply in maze.supplies}
    visited = [cell for cell in cells if cell in supplies]
    coins = spec.start_coins - steps + maze.supplies_on_path(cells)
    assert coins == spec.expected_coins
    if spec.number == 4:
        assert len(set(visited)) == len(maze.supplies) == 1, "the final route must collect the chest"
    if spec.number == 2:
        assert visited == [], "the direct L2 route skips the optional chest"
    assert "move_one_step_" in spec.reference_code
    assert "turn_" not in spec.reference_code
    assert "input(" not in spec.reference_code


def test_four_levels_get_harder():
    assert SPECS[0].direct_coins > 0 and SPECS[1].direct_coins > 0
    assert 0 < SPECS[2].direct_coins < 10, "level 3 must be a tight but survivable budget"
    assert all(spec.direct_coins <= 0 for spec in SPECS[3:]), "the final level needs a detour"
    assert [spec.number for spec in SPECS] == [1, 2, 3, 4]
    assert len({spec.name for spec in SPECS}) == 4


def test_level_one_is_a_five_step_start():
    spec = SPECS[0]
    maze = Maze.from_ascii(spec.maze_ascii)
    assert spec.shortest_steps == 5
    assert len(maze.shortest_path()) - 1 == 5
    assert spec.expected_steps == 5


def test_maps_have_enough_supplies_for_their_economy(spec, maze):
    total = sum(supply.value for supply in maze.supplies)
    assert spec.start_coins + total >= spec.shortest_steps


def test_maze_rejects_ragged_rows():
    with pytest.raises(MazeError):
        Maze.from_ascii("###\n#S#\n#B##")


def test_maze_requires_start_and_base():
    with pytest.raises(MazeError):
        Maze.from_ascii("###\n#.#\n###")


def test_boss_map_puts_the_pad_two_above_the_boss():
    maze = Maze.from_ascii(mission_one.BOSS_MAZE_ASCII)
    assert maze.start == (1, 1)
    assert maze.base == (17, 7)
    assert maze.goal == (17, 5)
    assert maze.base[0] == maze.goal[0] and maze.goal[1] == maze.base[1] - 2
    path = maze.shortest_path_to(maze.goal)
    assert path[-1] == maze.goal
    assert len(path) - 1 == mission_one.BOSS_SPEC.shortest_steps == 20


def test_goal_tile_is_optional_and_needs_no_base_route():
    maze = Maze.from_ascii(mission_one.LEVELS[0].maze_ascii)
    assert maze.goal is None


def test_goal_must_be_unique_and_reachable():
    with pytest.raises(MazeError):
        Maze.from_ascii("#######\n#S.GG.#\n#B....#\n#######")
    with pytest.raises(MazeError):
        Maze.from_ascii("#######\n#S#..G#\n#B#####\n#######")
