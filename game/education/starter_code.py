"""Per-stage editor helpers.

Every editor starts empty: students write the program themselves.  The game
supplies the mission brief, a permanent command reference and progressive
hints, but never the answer code (that lives in ``answers/answer_key.html``).
"""

CREATE_CODE = ""
MAZE_CODE = ""
BOSS_CODE = ""

STARTER_CODE = {
    1: CREATE_CODE,
    2: MAZE_CODE,
    3: BOSS_CODE,
}

# (code, note) pairs shown in the permanent command strip above the editor.
COMMANDS_BY_STAGE = {
    1: [
        ('input("...")', "ask for text"),
        ("print(...)", "show a message"),
        ("player_name", "store the name"),
    ],
    2: [
        ("move_one_step_up()", "up, 1 coin"),
        ("move_one_step_down()", "down, 1 coin"),
        ("move_one_step_left()", "left, 1 coin"),
        ("move_one_step_right()", "right, 1 coin"),
        ("coins", "coins you have"),
        ("print(...)", "show a message"),
    ],
    3: [
        ("move_one_step_up()", "up, 1 coin"),
        ("move_one_step_down()", "down, 1 coin"),
        ("move_one_step_left()", "left, 1 coin"),
        ("move_one_step_right()", "right, 1 coin"),
        ("fire_super_attack()", "launch the beam"),
        ("coins", "check coins"),
    ],
}

EDITOR_PLACEHOLDER = {
    1: "Write your mission code here.",
    2: "Write your route here - the commands are above.",
    3: "Walk to the attack pad, then write super_attack() here.",
}

HELP_LINES = [
    ("Game commands", [
        "move_one_step_up()     move one tile up (costs 1 coin)",
        "move_one_step_down()   move one tile down (costs 1 coin)",
        "move_one_step_left()   move one tile left (costs 1 coin)",
        "move_one_step_right()  move one tile right (costs 1 coin)",
        "fire_super_attack()    launch the beam from the attack pad",
    ]),
    ("Game values", [
        "coins            your current coins",
        "player_name      the name you chose",
        "weapon_power     fixed at 5 for this mission",
    ]),
    ("Python commands", [
        "input(\"question\")  ask the player for text",
        "int(text)          turn number text into a number",
        "for i in range(n): repeat the indented lines n times",
        "def name():        create your own function",
    ]),
    ("Mission rules", [
        "Every move costs 1 coin - up, down, left or right.",
        "Gold coin = +10 coins. Treasure chest = +20 coins.",
        "Reach the base before your coins run out. Four levels, easy to hard.",
        "The final base tops you up to 50 coins for the boss.",
        "Boss: walk to the attack pad, then fire inside if coins >= 30:",
        "Stuck? Press the Hint button beside the mission title.",
    ]),
]
