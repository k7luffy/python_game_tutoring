"""Grid maze model: loading, collision and route helpers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

WALL = "#"
FLOOR = "."
START = "S"
BASE = "B"
COIN = "c"
CHEST = "C"
GOAL = "G"

WALKABLE_TILES = {FLOOR, START, BASE, COIN, CHEST, GOAL}
# Supplies are exposed with readable kind names; the raw map letters still work.
KIND_NAMES = {COIN: "coin", CHEST: "chest"}
SUPPLY_VALUES = {COIN: 10, CHEST: 20, "coin": 10, "chest": 20}
SUPPLY_NAMES = {
    COIN: "Gold Coin", CHEST: "Treasure Chest",
    "coin": "Gold Coin", "chest": "Treasure Chest",
}


class MazeError(ValueError):
    """Raised when a maze layout is malformed."""


@dataclass(frozen=True)
class Supply:
    x: int
    y: int
    kind: str

    @property
    def value(self) -> int:
        return SUPPLY_VALUES[self.kind]

    @property
    def name(self) -> str:
        return SUPPLY_NAMES[self.kind]


class Maze:
    """An immutable grid layout with a start tile and an enemy base."""

    def __init__(self, rows: list[str]) -> None:
        if not rows:
            raise MazeError("The maze is empty.")
        width = len(rows[0])
        for index, row in enumerate(rows):
            if len(row) != width:
                raise MazeError(
                    f"Row {index} is {len(row)} tiles wide but row 0 is {width}."
                )
        self.rows = tuple(rows)
        self.width = width
        self.height = len(rows)
        self.start = self._find_single(START)
        self.base = self._find_single(BASE)
        self.goal = self._find_goal()
        self.supplies = self._find_supplies()
        self._validate()

    # ------------------------------------------------------------ building
    @classmethod
    def from_ascii(cls, text: str) -> "Maze":
        lines = [line.rstrip() for line in text.strip("\n").splitlines()]
        return cls(lines)

    def _find_single(self, char: str) -> tuple[int, int]:
        found = [
            (x, y)
            for y, row in enumerate(self.rows)
            for x, cell in enumerate(row)
            if cell == char
        ]
        if len(found) != 1:
            label = {START: "start tile (S)", BASE: "base tile (B)"}[char]
            raise MazeError(f"The maze needs exactly one {label}, found {len(found)}.")
        return found[0]

    def _find_goal(self) -> tuple[int, int] | None:
        found = [
            (x, y)
            for y, row in enumerate(self.rows)
            for x, cell in enumerate(row)
            if cell == GOAL
        ]
        if len(found) > 1:
            raise MazeError(
                f"The maze allows at most one goal tile (G), found {len(found)}."
            )
        return found[0] if found else None

    def _find_supplies(self) -> tuple[Supply, ...]:
        supplies = []
        for y, row in enumerate(self.rows):
            for x, cell in enumerate(row):
                if cell in SUPPLY_VALUES:
                    supplies.append(Supply(x, y, KIND_NAMES.get(cell, cell)))
        return tuple(supplies)

    def _validate(self) -> None:
        unknown = {
            cell
            for row in self.rows
            for cell in row
            if cell not in WALKABLE_TILES and cell != WALL
        }
        if unknown:
            raise MazeError(f"Unknown maze tiles: {sorted(unknown)}")
        for x in range(self.width):
            if self.tile(x, 0) != WALL or self.tile(x, self.height - 1) != WALL:
                raise MazeError("The maze needs a wall all the way around the edge.")
        for y in range(self.height):
            if self.tile(0, y) != WALL or self.tile(self.width - 1, y) != WALL:
                raise MazeError("The maze needs a wall all the way around the edge.")
        distances = self.distances_from(self.start)
        if self.base not in distances:
            raise MazeError("The base cannot be reached from the start tile.")
        if self.goal is not None:
            if self.goal in (self.start, self.base):
                raise MazeError("The goal tile cannot be the start or the base.")
            if self.goal not in distances:
                raise MazeError("The goal cannot be reached from the start tile.")
        for supply in self.supplies:
            if (supply.x, supply.y) not in distances:
                raise MazeError(
                    f"Supply at ({supply.x}, {supply.y}) cannot be reached from the start."
                )

    # ------------------------------------------------------------ queries
    def tile(self, x: int, y: int) -> str:
        return self.rows[y][x]

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_wall(self, x: int, y: int) -> bool:
        if not self.is_inside(x, y):
            return True
        return self.tile(x, y) == WALL

    def is_walkable(self, x: int, y: int) -> bool:
        return not self.is_wall(x, y)

    def supply_at(self, x: int, y: int) -> Supply | None:
        for supply in self.supplies:
            if supply.x == x and supply.y == y:
                return supply
        return None

    def floor_positions(self) -> list[tuple[int, int]]:
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.tile(x, y) != WALL
        ]

    # ------------------------------------------------------------ routing
    def distances_from(self, origin: tuple[int, int]) -> dict[tuple[int, int], int]:
        distances = {origin: 0}
        queue: deque[tuple[int, int]] = deque([origin])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = x + dx, y + dy
                if self.is_walkable(nx, ny) and (nx, ny) not in distances:
                    distances[(nx, ny)] = distances[(x, y)] + 1
                    queue.append((nx, ny))
        return distances

    def shortest_path(self) -> list[tuple[int, int]]:
        """Shortest route of tiles from the start to the base (inclusive)."""
        return self.shortest_path_to(self.base)

    def shortest_path_to(self, target: tuple[int, int]) -> list[tuple[int, int]]:
        """Shortest route of tiles from the start to ``target`` (inclusive)."""
        distances = self.distances_from(self.start)
        if target not in distances:
            return []
        path = [target]
        x, y = target
        while (x, y) != self.start:
            step = distances[(x, y)] - 1
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = x + dx, y + dy
                if distances.get((nx, ny)) == step:
                    x, y = nx, ny
                    path.append((x, y))
                    break
        path.reverse()
        return path

    def shortest_steps(self) -> int:
        path = self.shortest_path()
        return max(0, len(path) - 1)

    def supplies_on_path(self, path: list[tuple[int, int]]) -> int:
        total = 0
        path_set = set(path)
        for supply in self.supplies:
            if (supply.x, supply.y) in path_set:
                total += supply.value
        return total


def path_to_ascii(maze: Maze, path: list[tuple[int, int]], marks: str = "*") -> str:
    """Debug helper: draw the maze with a route overlaid."""
    path_set = set(path)
    lines = []
    for y in range(maze.height):
        row = []
        for x in range(maze.width):
            cell = maze.tile(x, y)
            if (x, y) in path_set and cell not in (START, BASE):
                row.append(marks)
            else:
                row.append(cell)
        lines.append("".join(row))
    return "\n".join(lines)
