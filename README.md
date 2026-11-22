# Python Maze Adventure — The Coin Mission

A complete 90-minute coding lesson for **Year 6 Digital Technologies** (students aged 11–12).
The lesson teaches Python first and uses the game as practice: students review variables,
comparisons and `if`/`else`, ask the player for a name with `input()`, turn text into numbers with `int()`, repeat
steps with a `for` loop, build their own `move_right(steps)` function, then plan routes
through four increasingly difficult maze levels and defeat the boss with an `if`/`else`
coin check after walking to an attack pad.

**Curriculum:** Australian Curriculum v9 Digital Technologies — **AC9TDI6P02**
*Design algorithms involving multiple alternatives (branching) and iteration.*

## What is included

| Item | Path | Purpose |
|---|---|---|
| Game | `game/main.py` | Pygame app with three stages, four maze levels and a live Python editor |
| Slides | `slides/index.html` | 24-slide knowledge-first deck with 12 interactive quizzes |
| Lesson plan | `lesson_plan/lesson_plan.md` | Full 90-minute teacher script, timing, differentiation and assessment |
| Answer key | `answers/answer_key.html` | Teacher-only Create code, four maze routes and Boss code — do not project |
| Homework | `homework/homework.pdf` | Three-page printable worksheet (white background, ink-saving); `homework.html` is the source |
| Tests | `tests/` | Automated game, sandbox, UI and document-consistency checks |

The slides, the game and the answer key are all self-contained and work offline.

## Requirements

- **Python 3.10 or newer** (built and tested with Python 3.14).
- **pygame-ce 2.5 or newer** — installed as the `pygame` module. pygame-ce is the
  community edition and is what this project is tested with. Classic `pygame` 2.x also
  imports under the same name, but pygame-ce is recommended for current Python versions.
- **pytest 8 or newer** — only needed to run the automated tests.

The package list is in `game/requirements.txt`:

```text
pygame-ce>=2.5,<3
pytest>=8
```

## Installation

### macOS or Linux

```bash
cd python_Arena
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r game/requirements.txt
```

### Windows

```bat
cd python_Arena
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r game/requirements.txt
```

## Launch the game

The easiest way is to double-click the launcher for your computer. The launcher starts
the game with a Python that already has pygame — the project `.venv` if it is working,
otherwise any `py -3`, `python` or `python3` on the machine — and only creates `.venv`
and installs the packages when no Python has pygame yet.

- **macOS:** double-click `run_game.command`.
- **Windows:** double-click `run_game.bat`.

Both launchers repair an environment that has lost pygame, rebuild a `.venv` copied from
another computer, and pause on an error so the message stays on screen. The game declares
per-monitor DPI awareness, so a Windows display scaled above 100% keeps a sharp window
rather than a blurry one.

Or run it from a terminal with the environment active:

```bash
# macOS and Linux
source .venv/bin/activate
python game/main.py
```

```bat
rem Windows
.venv\Scripts\activate
python game\main.py
```

Starting `game/main.py` with a Python that does not have pygame prints a message that
names that Python and points back to the launcher.

The game opens in a resizable window at 1280 × 800. The drawing canvas is 1440 × 900 and
scales to fit. The left side is the arena; the right side is the code editor. Every stage
opens with an **empty editor**: the game supplies the mission, a permanent command strip
and progressive hints, never the answer code.

### Game controls

| Action | Keys |
|---|---|
| Run the program | **Ctrl + Enter** (or **Cmd + Enter** on macOS) |
| Stop the program | **Ctrl/Cmd + Enter** again, **Esc**, or the **Stop** button |
| Help and command reference | **F1** |
| Full screen | **F11** |
| Indent in the editor | **Tab** (auto-indents after a colon) |
| Undo / redo | **Ctrl/Cmd + Z** / **Ctrl/Cmd + Shift + Z** |
| Reset the current level or stage | the **Reset** button |
| Speed | **1x → 2x → Instant** button |
| Sound | **Sound / Muted** button in the header |
| Progressive hints | the **Hint** button beside the mission title |
| Preview a maze level | click the level dots (**1–4**) on the Maze stage |

### The three stages

| Stage | Title | What students do |
|---|---|---|
| 1 | **Create Your Explorer** | Use `input()` to ask for a name and `print()` a welcome that includes it, writing the program from an empty editor; the game fixes `weapon_power` at 5 |
| 2 | **Escape the Maze** | Plan routes through four levels; every move costs 1 coin; collect gold coins (+10) and treasure chests (+20); reach the base before the coins run out |
| 3 | **Super Attack** | Walk from the top-left start to the cyan attack pad above the boss, then write `super_attack()` with `if coins >= 30:` and call `fire_super_attack()` to defeat the boss |

### The four maze levels

| # | Level | Start coins | New challenge |
|---|---|---|---|
| 1 | First Steps | 30 | A five-step corridor — walk right to the base |
| 2 | Two Paths | 35 | Two routes; the chest is optional and pays +20 |
| 3 | Save Your Coins | 22 | The shortest route costs 26, so the coin on the route is compulsory |
| 4 | The Chest Detour | 33 | The final level: the shortest route runs out of coins; only a dead-end chest pays for the long way |

Reaching the base passes the level; running out of coins before the base fails it. The
final base tops the player up to exactly **50 coins**, and a Boss practice run starts with
the same 50. Every Boss move also costs 1 coin: the shortest walk from the start to the
attack pad is 20 steps, so the robot arrives with exactly 30 coins.

The game commands are the four one-step moves `move_one_step_up()`,
`move_one_step_down()`, `move_one_step_left()` and `move_one_step_right()` (each costs
1 coin and turns the robot that way), plus `fire_super_attack()`. There are no turning
commands and no command arguments: repeat a direction with a `for` loop or a helper such
as `move_right(steps)`. The game values are `coins`, `player_name` and `weapon_power`
(fixed at 5 in the Create mission). On the Boss stage `fire_super_attack()` only works
when the robot stands on the attack pad and the call sits inside an
`if coins >= 30:` check.
The **Hint** button reveals one idea at a time — never the full program. On the last maze
hint, students may optionally reveal the reference route on the map.

## Launch the slides

1. Double-click `slides/index.html` — it opens in any modern browser.
2. Press **F** for full screen.
3. Use **→ / Space / Page Down** and **← / Page Up** to move, **Home / End** to jump,
   **N** for presenter notes, **B** for a blackout, **R** to reset the quizzes and **?**
   for the key list.
4. Quizzes are interactive: choose an option, read the feedback, try again after a wrong
   answer, and use **Reset** (or **R**) to clear every quiz before the next class.
5. Add a hash such as `#12` to the address to open a particular slide. The deck works
   completely offline: all CSS, JavaScript, quizzes and sprites are inside the one file.

The deck follows the lesson order **review → input → for loops → functions → game**. The
game appears only on slides 21–22, after the knowledge has been taught.

## Teacher answer key

`answers/answer_key.html` is a separate, offline teacher page containing the Create
program, the four maze reference routes and the Boss program. It is visibly marked
**Teacher answer key — do not project**. Open it in a browser or print it; it contains no
external assets. Regenerate it from the mission data after changing a level:

```bash
.venv/bin/python tools/build_answer_key.py
```

## Run the tests

From the project folder, with the virtual environment active:

```bash
python -m pytest tests/ -q
```

The tests run headlessly (dummy SDL drivers), so no window or sound device is needed.
They cover the four-level maze economy, every reference route, progressive hints, sandbox
limits, session rules, empty-editor behaviour, friendly error messages, the full
Create → four levels → Boss campaign, the answer key, and consistency between the game,
the slides, the lesson plan and this README.

## Project layout

```text
python_Arena/
├── game/
│   ├── main.py              application entry point
│   ├── engine/              constants, maze, sandbox, execution bridge, session
│   ├── education/           empty starter code, command reference, error cards
│   ├── missions/            four level maps, hints and teacher reference routes
│   ├── ui/                  arena, editor, console, modals, widgets
│   ├── assets/              generated sprites and icon
│   ├── tools/               asset builder
│   └── requirements.txt
├── tests/                   pytest suite
├── answers/
│   └── answer_key.html      teacher-only answer key
├── homework/
│   ├── homework.pdf         printable three-page worksheet
│   └── homework.html        source for the worksheet
├── lesson_plan/
│   └── lesson_plan.md
├── slides/
│   └── index.html
├── tools/
│   └── build_answer_key.py  rebuilds the answer key from the mission data
├── README.md
├── run_game.command
└── run_game.bat
```

## Troubleshooting

- **"python: command not found"** — install Python 3.10 or newer from python.org, then
  create the virtual environment again. On Windows the command may be `py -3`.
- **The Windows window flashes and closes, or cmd says "The system cannot find the batch
  label specified"** — use the latest project files: `run_game.bat` now uses Windows (CRLF)
  line endings and finds `py -3`, `python` or `python3` automatically. If it still fails,
  open Command Prompt in the project folder and run `py -3 game\main.py` to read the message.
- **The window or text is blurry on Windows** — the game asks SDL for per-monitor DPI
  awareness; use the latest files, and press **F11** for full screen on a scaled laptop screen.
- **"No module named 'pygame'"** — the Python that started the game is not the one with
  pygame, which is common on a laptop with more than one Python installed. Use the
  launcher: `run_game.bat` finds a Python that already has pygame, or sets up `.venv` if
  none has it. To see which Python has pygame, run
  `py -3 -c "import pygame; print(pygame.version.ver)"`.
- **"No module named pygame" inside an activated environment** — the environment is
  missing the package. Run `python -m pip install -r game/requirements.txt` in it, or
  delete `.venv` and let the launcher build it again.
- **The window is too large or too small** — the game is resizable. Drag the window edge,
  or press **F11** for full screen. The canvas keeps its 16:9 shape.
- **No sound in class** — click **Sound** to switch to **Muted**. The game is fully usable
  silently.
- **The slides do not change** — click the deck first so the browser has keyboard focus.
  Then use the arrow keys, Space, Page Up/Page Down, or click the left/right side. Clicking
  inside a quiz answers it instead of changing slides, by design.
- **A quiz will not reset** — press **R** anywhere outside an answer button, or use the
  quiz's own **Reset** button.
- **Package installation fails** — check the internet connection for the first install
  only; after that the game, slides and answer key run offline. On managed school laptops,
  ask IT to allow `python -m pip install`.
- **Tests fail on a school machine** — tests force dummy SDL audio and video drivers and
  need no display. Run them from the project folder so `tests/conftest.py` can put `game/`
  on the import path.

## Limitations

- The project contains one campaign (the Coin Mission): Create, four maze levels and the
  Boss. There is no save file; code is kept while the app is open but is not stored
  between launches.
- The sandbox deliberately blocks imports, classes and private names, and limits programs
  to 200 game actions and 20 seconds of run time. It is a teaching tool, not a general
  Python environment.
- The slides are designed for a 16:9 screen; on very small laptop screens the stage scales
  down and code text becomes smaller.
