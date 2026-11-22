"""Mission 1 - The Coin Mission.

Four maze levels share one rule set.  The maps are ASCII art so a teacher can
edit them:
    #  stone wall        .  floor
    S  robot start       B  enemy base
    c  gold coin (+10)   C  treasure chest (+20)
    G  attack pad (Boss arena only)

The routes in this module are teacher answers.  They are used by the answer
key and the tests; the game itself starts every editor empty.
"""

from __future__ import annotations

from dataclasses import dataclass

MISSION_TITLE = "The Coin Mission"


def route_code(route: tuple[tuple[str, int], ...]) -> str:
    """Turn a route of (direction, count) moves into readable Python."""
    lines: list[str] = []
    for direction, count in route:
        if count <= 0:
            continue
        call = f"move_one_step_{direction}()"
        if count == 1:
            lines.append(call)
        else:
            lines.append(f"for i in range({count}):")
            lines.append(f"    {call}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class LevelSpec:
    """One maze level plus the teacher-only reference route."""

    number: int
    name: str
    maze_ascii: str
    start_coins: int
    objective: str
    hints: tuple[str, ...]
    route: tuple[tuple[str, int], ...]
    shortest_steps: int
    direct_coins: int
    expected_steps: int
    expected_coins: int

    @property
    def reference_code(self) -> str:
        return route_code(self.route)


LEVELS: tuple[LevelSpec, ...] = (
    LevelSpec(
        number=1,
        name="First Steps",
        maze_ascii='''
###################
#S.c..B############
###################
''',
        start_coins=30,
        objective=(
            "Reach the base five steps to the right. Every step costs 1 coin; "
            "the gold coin on the way pays +10."
        ),
        hints=(
            "The base is five steps to the right. Every step costs 1 coin.",
            "Walk across the gold coin on the way: it pays +10 coins.",
            "Call move_one_step_right() five times, or put it in a for loop.",
        ),
        route=(("right", 5),),
        shortest_steps=5,
        direct_coins=35,
        expected_steps=5,
        expected_coins=35,
    ),
    LevelSpec(
        number=2,
        name="Two Paths",
        maze_ascii='''
###################
#S................#
#....#####...####.#
#....#...#...#....#
#....#...#...#..C.#
#....#...#...#....#
#........#........#
#........#.......B#
###################
''',
        start_coins=35,
        objective=(
            "More than one route reaches the base. The chest is optional, but it pays +20."
        ),
        hints=(
            "The short route reaches the base, but the chest is worth +20.",
            "The chest sits north of the long corridor. A detour costs only a few extra steps.",
            "Try the direct route first, then compare the coins with a chest detour.",
        ),
        route=(("right", 16), ("down", 6)),
        shortest_steps=22,
        direct_coins=13,
        expected_steps=22,
        expected_coins=13,
    ),
    LevelSpec(
        number=3,
        name="Save Your Coins",
        maze_ascii='''
###################
#S....#...........#
#.....#.....#.....#
#.....#.....#..c..#
#.....#.....#.....#
#.....#.....#.....#
#.......c...#.....#
#.....#.....#....B#
#.....#.....#.....#
#.....#...........#
###################
''',
        start_coins=22,
        objective=(
            "The shortest route costs 26 coins, but you only start with 22. "
            "Find the gold coin on the route."
        ),
        hints=(
            "You start with 22 coins and the shortest route costs 26.",
            "There is a gold coin on the shortest route.",
            "Plan each move so the route passes through the coin.",
        ),
        route=(
            ("right", 4), ("down", 5), ("right", 6),
            ("down", 3), ("right", 6), ("up", 2),
        ),
        shortest_steps=26,
        direct_coins=6,
        expected_steps=26,
        expected_coins=6,
    ),
    LevelSpec(
        number=4,
        name="The Chest Detour",
        maze_ascii='''
###################
#S....#.....#...#C#
#.#.#.#.###.#.#.#.#
#...#...#.#...#...#
#########.#######.#
#...#.#.......#...#
#.#.#.#.###.###.###
#.#...#...#.......#
#.#######.#######.#
#................B#
###################
''',
        start_coins=33,
        objective=(
            "The shortest route costs 36 coins and you have 33. "
            "The chest in the top-right dead end pays +20, but the detour is long."
        ),
        hints=(
            "You start with 33 coins and the shortest route costs 36.",
            "The chest sits in the top-right dead end. Reach it from below.",
            "The chest route is 40 steps and pays +20. Plan every move.",
        ),
        route=(
            ("right", 4), ("down", 2), ("right", 2), ("up", 2),
            ("right", 4), ("down", 2), ("right", 2), ("up", 2),
            ("right", 2), ("down", 2), ("right", 2), ("up", 2),
            ("down", 4), ("left", 2), ("down", 2), ("right", 2),
            ("down", 2),
        ),
        shortest_steps=36,
        direct_coins=-3,
        expected_steps=40,
        expected_coins=13,
    ),
)

# The first map is also handy for UI previews and older imports.
MAZE_ASCII = LEVELS[0].maze_ascii

_DIR_DX = (0, 1, 0, -1)
_DIR_DY = (-1, 0, 1, 0)
_DIR_INDEX = {"up": 0, "right": 1, "down": 2, "left": 3}


def reference_path(maze, spec: "LevelSpec") -> list[tuple[int, int]]:
    """Turn a reference route into the list of cells the robot visits.

    Used by the hint overlay and by tests, so the drawn route can never
    disagree with the answer code.
    """
    x, y = maze.start
    cells = [(x, y)]
    for direction, count in spec.route:
        if direction not in _DIR_INDEX:
            raise ValueError(f"unknown route direction {direction!r}")
        dx, dy = _DIR_DX[_DIR_INDEX[direction]], _DIR_DY[_DIR_INDEX[direction]]
        for _ in range(count):
            nx, ny = x + dx, y + dy
            if maze.is_wall(nx, ny):
                raise ValueError(f"reference route walks into a wall at {(nx, ny)}")
            x, y = nx, ny
            cells.append((x, y))
    return cells


OBJECTIVE_CREATE = (
    "Ask the player for a name with input(), store it in player_name, "
    "then print a welcome that includes the name. "
    "Your weapon power is fixed at 5."
)

OBJECTIVE_MAZE = (
    "Guide your robot to the enemy base. Every step costs 1 coin, "
    "so collect supplies on the way!"
)

OBJECTIVE_BOSS = (
    "Walk from the start to the cyan attack pad above the boss. "
    "Every step costs 1 coin. Then write super_attack() with an "
    "if coins >= 30 check and call it."
)

TIPS_CREATE = [
    "input() always gives you text (a string).",
    "Store the answer in player_name before you print it.",
    "The game fixes your weapon power at 5, so you only ask for the name.",
]

TIPS_MAZE = [
    "Golden coin = +10 coins. Treasure chest = +20 coins.",
    "Every move costs 1 coin - up, down, left or right.",
    "Stuck? Open the Hint button beside the mission title.",
]

TIPS_BOSS = [
    "The attack pad is two tiles above the boss.",
    "Every step costs 1 coin. The shortest walk is 20 steps.",
    "Use if coins >= 30: ... else: ... inside your function.",
]

HINTS_CREATE = (
    "input() asks the question and waits for the player to type an answer.",
    "Store the answer in player_name so the program can use it again.",
    "Print a welcome message that includes player_name.",
)

HINTS_BOSS = (
    "Walk to the cyan attack pad above the boss. Every step costs 1 coin.",
    "At the pad, check your coins with if coins >= 30: ... else: ...",
    "Call fire_super_attack() inside the if, then call super_attack().",
)

L2_CHEST_ROUTE = (
    ("right", 16), ("down", 3), ("left", 1),
    ("right", 1), ("down", 3),
)
L2_CHEST_DETOUR = route_code(L2_CHEST_ROUTE)

BOSS_ROUTE: tuple[tuple[str, int], ...] = (
    ("right", 4), ("down", 2), ("right", 6), ("down", 1),
    ("right", 6), ("down", 1),
)
BOSS_ROUTE_CODE = route_code(BOSS_ROUTE)

BOSS_MAZE_ASCII = '''
###################
#S....#......######
##.##.#.....#######
#####.......#######
#####.#####.......#
#.....###.###....G#
#...#####.###.....#
#............####B#
###################
'''

BOSS_SPEC = LevelSpec(
    number=5,
    name="Boss Arena",
    maze_ascii=BOSS_MAZE_ASCII,
    start_coins=50,
    objective=OBJECTIVE_BOSS,
    hints=HINTS_BOSS,
    route=BOSS_ROUTE,
    shortest_steps=20,
    direct_coins=0,
    expected_steps=20,
    expected_coins=30,
)

CREATE_SOLUTION = '''\
player_name = input("What is your name? ")
print("Welcome,", player_name)
'''

BOSS_SOLUTION = '''\
def super_attack():
    if coins >= 30:
        print("Super Attack Activated!")
        fire_super_attack()
    else:
        print("Not enough coins!")

super_attack()
'''

BOSS_ANSWER = BOSS_ROUTE_CODE + "\n" + BOSS_SOLUTION

SUPPLY_LEGEND = [
    ("Gold Coin", "+10 coins"),
    ("Treasure Chest", "+20 coins"),
]
