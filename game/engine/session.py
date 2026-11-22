"""Game rules, stage flow and student-run orchestration.

The session owns the world (robot, coins, supplies, boss) and turns the
stream of requests from :class:`engine.sandbox.StudentRunner` into animated
actions.  It never blocks: the UI calls :meth:`update` once per frame.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from engine import constants as C
from engine.bridge import Bridge, Request
from engine.maze import Maze
from engine.sandbox import ConsoleBuffer, RunOutcome, StudentRunner
from missions import mission_one
from education.errors import ErrorCard


@dataclass
class Player:
    x: int
    y: int
    facing: int = 0
    steps: int = 0

    def ahead(self) -> tuple[int, int]:
        return (
            self.x + C.DIRECTION_DX[self.facing],
            self.y + C.DIRECTION_DY[self.facing],
        )


@dataclass
class Effect:
    kind: str            # pickup | bump | beam | explode | fizzle | confetti
    start: float
    duration: float
    x: int = 0
    y: int = 0
    text: str = ""
    colour: tuple = C.COL_GOLD

    def progress(self, now: float) -> float:
        if self.duration <= 0:
            return 1.0
        return max(0.0, min(1.0, (now - self.start) / self.duration))

    def finished(self, now: float) -> bool:
        return now - self.start >= self.duration


@dataclass
class MoveAnim:
    start: float
    duration: float
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    facing_from: int
    facing_to: int
    turn_only: bool = False

    def progress(self, now: float) -> float:
        if self.duration <= 0:
            return 1.0
        return max(0.0, min(1.0, (now - self.start) / self.duration))


@dataclass
class Notice:
    kind: str            # success | failure | info
    title: str
    lines: list[str] = field(default_factory=list)
    action: str | None = None   # "next_stage" | None


class Session:
    """One lesson session: three stages, many runs."""

    def __init__(self, maze: Maze | None = None, clock=time.monotonic) -> None:
        if maze is None:
            self.level_specs = list(mission_one.LEVELS)
            self.levels = [Maze.from_ascii(spec.maze_ascii) for spec in self.level_specs]
        else:
            self.level_specs = [mission_one.LEVELS[0]]
            self.levels = [maze]
        self.boss_spec = mission_one.BOSS_SPEC
        self.boss_maze = Maze.from_ascii(self.boss_spec.maze_ascii)
        self.level_index = 0
        self.levels_done: set[int] = set()
        self.maze = self.levels[0]
        self.custom_maze = maze is not None
        self.clock = clock
        self.console = ConsoleBuffer()
        self.stage = C.STAGE_CREATE
        self.speed_index = 0
        self.player_name = "Explorer"
        self.weapon_power = C.DEFAULT_WEAPON_POWER
        self.has_character = False
        self.maze_done = False
        self.boss_done = False
        self.checkpoint_coins = 0
        self.practice_run = False
        self.run_state = C.RUN_IDLE
        self.runner: StudentRunner | None = None
        self.outcome: RunOutcome | None = None
        self.notice: Notice | None = None
        self.error_card: ErrorCard | None = None
        self.pending: Request | None = None
        self.pending_until = 0.0
        self.pending_result: object = None
        self.waiting_input: Request | None = None
        self.anim: MoveAnim | None = None
        self.effects: list[Effect] = []
        self.sounds: list[str] = []
        self.last_activity = clock()
        self.run_started_at = 0.0
        self.stopped_by_user = False
        self.setup_world()

    # ------------------------------------------------------------ world setup
    @property
    def speed(self) -> float:
        return C.SPEED_OPTIONS[self.speed_index][0]

    def cycle_speed(self) -> None:
        self.speed_index = (self.speed_index + 1) % len(C.SPEED_OPTIONS)

    def setup_world(self) -> None:
        """Reset the visible world for the current stage."""
        self.player = Player(*self.maze.start, facing=0)
        self.steps = 0
        self.supplies_left = {(s.x, s.y): s for s in self.maze.supplies}
        self.collected: list[str] = []
        self.reached_base = False
        self.reached_goal = False
        self.mission_failed = False
        self.boss_hp = 100
        self.boss_defeated = False
        self.attack_fired = False
        self.attack_off_pad = False
        self.attack_unguarded = False
        self.practice_run = False
        if self.stage == C.STAGE_CREATE:
            self.coins = self.level_specs[0].start_coins
        elif self.stage == C.STAGE_MAZE:
            self.coins = self.level_specs[self.level_index].start_coins
        else:
            self.player.facing = 1
            if self.maze_done:
                self.coins = max(self.checkpoint_coins, 0)
            else:
                self.coins = C.PRACTICE_COINS
                self.practice_run = True
        self.anim = None
        self.effects = []

    def select_stage(self, stage: int) -> None:
        self.stop_run(silent=True)
        self.stage = max(1, min(C.STAGE_COUNT, stage))
        if self.stage == C.STAGE_CREATE:
            self.maze = self.levels[0]
        elif self.stage == C.STAGE_MAZE:
            self.maze = self.levels[self.level_index]
        else:
            self.maze = self.boss_maze
        self.notice = None
        self.error_card = None
        self.console.clear()
        self.console.add(mission_one_objective_title(self.stage), "system")
        if self.stage == C.STAGE_MAZE:
            self.console.add(self.level_label(), "system")
        self.setup_world()

    def select_level(self, index: int) -> None:
        """Teacher shortcut / level dots: jump to any maze level."""
        self.stop_run(silent=True)
        self.level_index = max(0, min(len(self.levels) - 1, index))
        self.maze = self.levels[self.level_index]
        self.stage = C.STAGE_MAZE
        self.notice = None
        self.error_card = None
        self.console.clear()
        self.console.add(self.level_label(), "system")
        self.setup_world()

    def advance_level(self) -> bool:
        """Move to the next maze level.  False when the final level is done."""
        if self.level_index + 1 >= len(self.levels):
            return False
        self.level_index += 1
        self.maze = self.levels[self.level_index]
        self.stage = C.STAGE_MAZE
        self.notice = None
        self.error_card = None
        self.console.clear()
        self.console.add(self.level_label(), "system")
        self.setup_world()
        return True

    def reset_stage(self) -> None:
        self.stop_run(silent=True)
        self.notice = None
        self.error_card = None
        self.setup_world()
        self.console.add("Stage restarted. Your code is still here.", "system")

    def reset_all(self) -> None:
        self.stop_run(silent=True)
        self.has_character = False
        self.maze_done = False
        self.boss_done = False
        self.checkpoint_coins = 0
        self.level_index = 0
        self.levels_done.clear()
        self.maze = self.levels[0]
        self.player_name = "Explorer"
        self.weapon_power = C.DEFAULT_WEAPON_POWER
        self.console.clear()
        self.select_stage(C.STAGE_CREATE)

    # ------------------------------------------------------------ run control
    def start_run(self, source: str) -> None:
        if self.run_state == C.RUN_RUNNING:
            return
        self.notice = None
        self.error_card = None
        self.console.clear()
        self.setup_world()
        self.console.add(mission_one_objective_title(self.stage), "system")
        self.console.add("Running your program...", "system")
        extra = {
            "coins": self.coins,
            "player_name": self.player_name,
            "weapon_power": self.weapon_power,
        }
        runner = StudentRunner(source, self._bridge(), self.console, extra_globals=extra, clock=self.clock)
        self.runner = runner
        self.outcome = None
        card = runner.compile()
        if card is not None:
            self.error_card = card
            self._log_card(card)
            self.run_state = C.RUN_FINISHED
            self.outcome = RunOutcome("blocked", card)
            self.notice = Notice(
                "error",
                card.title,
                [card.message] + ([card.hint] if card.hint else []),
            )
            return
        self.run_state = C.RUN_RUNNING
        self.stopped_by_user = False
        self.run_started_at = self.clock()
        self.last_activity = self.run_started_at
        runner.start()

    def _bridge(self) -> Bridge:
        if not hasattr(self, "_bridge_obj"):
            self._bridge_obj = Bridge(clock=self.clock)
        return self._bridge_obj

    def stop_run(self, silent: bool = False) -> None:
        if self.runner is not None:
            self.runner.stop()
        if self.pending is not None:
            self._bridge().respond(self.pending, None)
            self.pending = None
        self.waiting_input = None
        self.anim = None
        self.run_state = C.RUN_IDLE if silent else C.RUN_FINISHED
        if not silent:
            self.stopped_by_user = True
            self.console.add("Program stopped.", "warn")

    # ------------------------------------------------------------ per-frame
    def update(self, now: float) -> None:
        # finish the action currently being animated
        if self.pending is not None and now >= self.pending_until:
            request = self.pending
            self.pending = None
            self._bridge().respond(request, self.pending_result)
            self.last_activity = now
        # expire effects
        if self.effects:
            self.effects = [e for e in self.effects if not e.finished(now)]
        if self.anim is not None and now - self.anim.start >= self.anim.duration:
            self.anim = None
        # accept the next action
        if self.run_state == C.RUN_RUNNING and self.pending is None and self.waiting_input is None:
            request = self._bridge().poll()
            if request is not None:
                self._handle(request, now)
        # watch for a worker that has stopped responding
        if self.run_state == C.RUN_RUNNING and self.waiting_input is None:
            if now - self.last_activity > 30.0 and self.runner and self.runner.running:
                self.console.add("The program seems stuck. Stopping it safely.", "error")
                self.stop_run(silent=True)
                self.run_state = C.RUN_FINISHED
                self.notice = Notice(
                    "failure",
                    "Program Stuck",
                    ["Your program stopped responding and was stopped safely.",
                     "Check for a loop that never ends."],
                )
        # notice when the worker has finished
        if self.run_state == C.RUN_RUNNING and self.runner is not None and self.runner.outcome is not None:
            self._finish_run(self.runner.outcome)

    # ------------------------------------------------------------ requests
    def _handle(self, request: Request, now: float) -> None:
        kind = request.kind
        if kind == "input":
            self.waiting_input = request
            self.last_activity = now
            return
        result: dict = {"coins": self.coins}
        duration = 0.0
        if kind == "move":
            direction = str(request.payload.get("direction", "up"))
            result, duration = self._handle_move(now, direction)
        elif kind == "attack":
            guarded = bool(request.payload.get("guarded", False))
            result, duration = self._handle_attack(now, guarded)
        else:
            result = {"coins": self.coins}
        duration = duration / self.speed if self.speed > 0 else 0.0
        self.pending = request
        self.pending_result = result
        self.pending_until = now + duration
        self.last_activity = now
        if duration <= 0:
            self.pending_until = now  # resolved on the next update tick

    def _handle_move(self, now: float, direction: str) -> tuple[dict, float]:
        player = self.player
        fx, fy = player.x, player.y
        before_facing = player.facing
        if direction not in C.DIRECTION_NAMES:
            return {"coins": self.coins, "moved": False, "blocked": "direction"}, 0.0
        facing = C.DIRECTION_NAMES.index(direction)
        player.facing = facing
        goal = self.maze.goal if self.stage == C.STAGE_BOSS else self.maze.base
        if self.coins <= 0:
            self.console.add("No coins left! Your robot cannot take another step.", "error")
            if (player.x, player.y) != goal:
                self.mission_failed = True
            self.effects.append(Effect("bump", now, 0.3, player.x, player.y, "0 coins", C.COL_RED))
            self._sound("error")
            return {"coins": self.coins, "moved": False, "blocked": "coins"}, 0.25
        tx = player.x + C.DIRECTION_DX[facing]
        ty = player.y + C.DIRECTION_DY[facing]
        if self.stage == C.STAGE_BOSS and (tx, ty) == self.maze.base:
            self.console.add(
                "The boss blocks that tile! Stand on the attack pad above it.", "warn"
            )
            self.effects.append(Effect("bump", now, 0.35, tx, ty, "BOSS", C.COL_RED))
            self._sound("bump")
            return {"coins": self.coins, "moved": False, "blocked": "boss"}, 0.30
        if self.maze.is_wall(tx, ty):
            self.console.add("BONK! A stone wall blocks the way. (No coins used.)", "warn")
            self.effects.append(Effect("bump", now, 0.35, tx, ty, "", C.COL_STONE_LIGHT))
            self._sound("bump")
            return {"coins": self.coins, "moved": False, "blocked": "wall"}, 0.30
        player.x, player.y = tx, ty
        player.steps += 1
        self.steps += 1
        self.coins -= 1
        supply = self.supplies_left.pop((tx, ty), None)
        picked = None
        if supply is not None:
            self.coins += supply.value
            picked = {"kind": supply.kind, "value": supply.value}
            self.collected.append(supply.name)
            self.console.add(
                f"You found a {supply.name}! +{supply.value} coins (you now have {self.coins}).",
                "ok",
            )
            self.effects.append(
                Effect("pickup", now, 0.9, tx, ty, f"+{supply.value}", C.COL_GOLD)
            )
            self._sound("coin" if supply.value == 10 else "chest")
        reached = goal is not None and (tx, ty) == goal
        if reached and self.stage == C.STAGE_BOSS and not self.reached_goal:
            self.reached_goal = True
            self.console.add(
                f"You reached the attack pad with {self.coins} coins! "
                f"The super attack needs {C.SUPER_ATTACK_COST}.",
                "ok",
            )
            self._sound("base")
            self.effects.append(Effect("confetti", now, 1.2, tx, ty, "", C.COL_CYAN))
        elif reached and self.stage != C.STAGE_BOSS and not self.reached_base:
            self.reached_base = True
            self.console.add(
                f"You reached the enemy base with {self.coins} coins!", "ok"
            )
            self._sound("base")
            self.effects.append(Effect("confetti", now, 1.2, tx, ty, "", C.COL_MAGENTA))
        if self.coins <= 0 and not reached:
            self.mission_failed = True
            self.console.add(
                "You ran out of coins! This mission attempt has failed.", "error"
            )
        elif self.coins > 0 and not reached:
            self._sound("step")
        self.anim = MoveAnim(
            start=now,
            duration=C.MOVE_SECONDS / self.speed if self.speed > 0 else 0.0,
            from_x=fx,
            from_y=fy,
            to_x=tx,
            to_y=ty,
            facing_from=before_facing,
            facing_to=player.facing,
        )
        return {
            "coins": self.coins,
            "moved": True,
            "blocked": None,
            "picked": picked,
            "at_base": reached and self.stage != C.STAGE_BOSS,
            "at_goal": reached and self.stage == C.STAGE_BOSS,
        }, C.MOVE_SECONDS

    def _handle_attack(self, now: float, guarded: bool) -> tuple[dict, float]:
        if self.stage != C.STAGE_BOSS:
            self.console.add("There is no boss to attack in this stage.", "warn")
            return {"coins": self.coins, "hit": False, "reason": "no boss"}, 0.2
        if self.boss_defeated:
            self.console.add("The boss is already defeated. Nice work!", "ok")
            return {"coins": self.coins, "hit": True, "reason": "already"}, 0.2
        pad = self.maze.goal
        if pad is not None and (self.player.x, self.player.y) != pad:
            self.attack_off_pad = True
            self.console.add(
                "The beam only works from the attack pad above the boss. "
                "(No coins used.)",
                "warn",
            )
            self.effects.append(
                Effect("bump", now, 0.35, self.player.x, self.player.y, "PAD", C.COL_CYAN)
            )
            self._sound("error")
            return {"coins": self.coins, "hit": False, "reason": "off_pad"}, 0.35
        if not guarded:
            self.attack_unguarded = True
            self.console.add(
                "The super attack needs an if coins >= 30: check around "
                "fire_super_attack(). (No coins used.)",
                "error",
            )
            self._sound("error")
            return {"coins": self.coins, "hit": False, "reason": "unguarded"}, 0.35
        self.attack_fired = True
        beam = C.BEAM_SECONDS
        if self.coins >= C.SUPER_ATTACK_COST:
            self.boss_hp = 0
            self.boss_defeated = True
            self.boss_done = True
            self.effects.append(Effect("beam", now, beam, self.player.x, self.player.y, "", C.COL_CYAN))
            self.effects.append(Effect("explode", now + beam * 0.55, 0.9, self.maze.base[0], self.maze.base[1]))
            self.console.add(
                f"Super attack launched with {self.coins} coins! The boss is defeated!", "ok"
            )
            self._sound("beam")
            return {"coins": self.coins, "hit": True, "reason": "hit"}, beam
        self.effects.append(Effect("fizzle", now, 0.8, self.maze.base[0], self.maze.base[1], "", C.COL_ORANGE))
        self.console.add(
            f"The beam fizzled! You need at least {C.SUPER_ATTACK_COST} coins, "
            f"but you only have {self.coins}.",
            "error",
        )
        self._sound("fizzle")
        return {"coins": self.coins, "hit": False, "reason": "coins"}, 0.8

    # ------------------------------------------------------------ input modal
    def submit_input(self, text: str) -> None:
        request = self.waiting_input
        if request is None:
            return
        self.waiting_input = None
        self.console.add(f"> {text}", "system")
        self.last_activity = self.clock()
        self._bridge().respond(request, text)

    def cancel_input(self) -> None:
        self.waiting_input = None
        self.stop_run()

    def _log_card(self, card) -> None:
        for line in card.console_lines():
            kind = "warn" if line.startswith("Tip:") else "error"
            self.console.add(line, kind)

    # ------------------------------------------------------------ finishing
    def _finish_run(self, outcome: RunOutcome) -> None:
        self.run_state = C.RUN_FINISHED
        self.outcome = outcome
        self.pending = None
        self.waiting_input = None
        if outcome.status == "cancelled":
            self.console.add("Program stopped.", "warn")
            return
        if outcome.card is not None:
            self.error_card = outcome.card
            self._log_card(outcome.card)
            self.notice = Notice(
                "error",
                outcome.card.title,
                [outcome.card.message] + ([outcome.card.hint] if outcome.card.hint else []),
            )
            return
        if self.stage == C.STAGE_CREATE:
            self._finish_create(outcome)
        elif self.stage == C.STAGE_MAZE:
            self._finish_maze(outcome)
        else:
            self._finish_boss(outcome)

    def _finish_create(self, outcome: RunOutcome) -> None:
        ns = outcome.namespace
        raw_name = ns.get("player_name", "")
        name = raw_name.strip()[:20] if isinstance(raw_name, str) else ""
        self.weapon_power = C.DEFAULT_WEAPON_POWER
        problems: list[str] = []
        if outcome.input_calls < 1:
            problems.append("Your program never asked for a name. Use input().")
        if "player_name" not in outcome.input_targets:
            problems.append(
                "Store the answer in player_name, like "
                'player_name = input("What is your name? ").'
            )
        if not name:
            problems.append("player_name is empty. Type a name in the input box when you run.")
        if "player_name" not in outcome.printed_names:
            problems.append('Print the name, like print("Welcome,", player_name).')
        if problems:
            self.console.add(" ".join(problems), "warn")
            self.notice = Notice(
                "info",
                "Almost there!",
                problems + ["Fix your code, then press Run Code again."],
            )
            return
        if name:
            self.player_name = name
        self.has_character = True
        self.console.add(
            f"Explorer {self.player_name} is ready. Weapon power is fixed at {self.weapon_power}.",
            "ok",
        )
        self.notice = Notice(
            "success",
            f"Welcome, {self.player_name}!",
            [
                f"Weapon power: {self.weapon_power} (fixed for this mission)",
                f"Starting coins: {self.level_specs[0].start_coins}",
                "Next mission: use movement commands to escape the maze.",
            ],
            action="next_stage",
        )
        self._sound("success")

    def _finish_maze(self, outcome: RunOutcome) -> None:
        spec = self.current_spec
        final = self.level_index + 1 >= len(self.levels)
        if self.reached_base:
            self.levels_done.add(self.level_index)
            self.console.add(
                f"Level {spec.number} complete! You reached the base with {self.coins} coins.",
                "ok",
            )
            if final:
                bonus = max(0, C.FINAL_BONUS_TARGET - self.coins)
                if bonus:
                    self.coins += bonus
                    self.console.add(
                        f"Base bonus: +{bonus} coins (the base tops you up to "
                        f"{C.FINAL_BONUS_TARGET}).",
                        "ok",
                    )
                self.checkpoint_coins = self.coins
                self.maze_done = True
                self.notice = Notice(
                    "success",
                    "All four levels cleared!",
                    [
                        f"{self.player_name} reached the final base.",
                        f"Checkpoint: {self.checkpoint_coins} coins for the super attack.",
                        f"The base tops every explorer up to {C.FINAL_BONUS_TARGET} coins.",
                        "Next: write your super_attack() function.",
                    ],
                    action="next_stage",
                )
            else:
                next_spec = self.level_specs[self.level_index + 1]
                self.notice = Notice(
                    "success",
                    f"Level {spec.number} complete!",
                    [
                        f"{self.player_name} reached the base with {self.coins} coins.",
                        f"Next level: {next_spec.name} "
                        f"({next_spec.start_coins} starting coins).",
                        "Press Next level when you are ready.",
                    ],
                    action="next_level",
                )
            self._sound("success")
        elif self.mission_failed or self.coins <= 0:
            self.notice = Notice(
                "failure",
                "Out of coins!",
                [
                    f"Level {spec.number}: {spec.name}.",
                    "Every step costs 1 coin and you have none left.",
                    "Restart the level and plan a route that collects supplies.",
                ],
            )
            self._sound("fail")
        else:
            self.console.add("Program finished. The robot has not reached the base yet.", "system")
            self.notice = Notice(
                "info",
                "Program finished",
                [
                    f"Coins left: {self.coins}",
                    "The robot did not reach the enemy base.",
                    "Check your route, then try again.",
                ],
            )

    def _finish_boss(self, outcome: RunOutcome) -> None:
        if self.boss_defeated:
            score = self.coins * 2 + self.weapon_power * 10
            self.console.add(
                f"BOSS DEFEATED! Final score: {score} points.", "ok"
            )
            self.notice = Notice(
                "success",
                "BOSS DEFEATED!",
                [
                    f"{self.player_name} saved the day!",
                    f"Coins left: {self.coins}   Weapon power: {self.weapon_power}",
                    f"Score: {score}",
                ],
            )
            self._sound("victory")
            return
        pad = self.maze.goal
        on_pad = pad is not None and (self.player.x, self.player.y) == pad
        if not on_pad:
            if self.coins <= 0:
                self.notice = Notice(
                    "failure",
                    "Out of coins!",
                    [
                        "Every move costs 1 coin and you have none left.",
                        "Reset the Boss stage and plan the shortest route.",
                        "The attack pad is the cyan tile two above the boss.",
                    ],
                )
                self._sound("fail")
            elif self.attack_off_pad:
                self.notice = Notice(
                    "info",
                    "Fire from the attack pad",
                    [
                        "Your program called fire_super_attack() away from the pad.",
                        "Walk onto the cyan attack pad, then call the beam from there.",
                        f"The shortest walk to the pad is {self.boss_spec.shortest_steps} steps.",
                    ],
                )
            elif self.attack_unguarded:
                self.notice = Notice(
                    "failure",
                    "Add the coin check",
                    [
                        "fire_super_attack() ran outside an if coins >= 30: check.",
                        "Put fire_super_attack() inside the if block, under the print.",
                    ],
                )
                self._sound("fail")
            else:
                self.notice = Notice(
                    "info",
                    "Reach the attack pad",
                    [
                        f"Coins left: {self.coins}",
                        "The attack pad is the cyan tile two above the boss.",
                        "Every step costs 1 coin. The shortest walk is "
                        f"{self.boss_spec.shortest_steps} steps.",
                    ],
                )
            return
        if self.attack_unguarded:
            self.notice = Notice(
                "failure",
                "Add the coin check",
                [
                    "fire_super_attack() ran outside an if coins >= 30: check.",
                    "Put fire_super_attack() inside the if block, under the print.",
                ],
            )
            self._sound("fail")
            return
        if self.attack_off_pad:
            self.notice = Notice(
                "info",
                "Fire from the attack pad",
                [
                    "Your program called fire_super_attack() away from the pad.",
                    "Walk onto the cyan pad, then call the beam from there.",
                ],
            )
            return
        if outcome.attack_calls == 0:
            if self.coins < C.SUPER_ATTACK_COST:
                self.notice = Notice(
                    "failure",
                    "Not enough coins",
                    [
                        f"You reached the pad with {self.coins} coins.",
                        f"The super attack needs {C.SUPER_ATTACK_COST}.",
                        "Every step costs 1 coin. Walk the shortest route: "
                        f"{self.boss_spec.shortest_steps} steps.",
                    ],
                )
                self._sound("fail")
                return
            if outcome.super_attack_called:
                lines = [
                    "Your super_attack() ran, but it never called fire_super_attack().",
                    "Put  fire_super_attack()  inside the if block, under the print.",
                ]
                self.notice = Notice("info", "The boss is still standing", lines)
                return
            if outcome.defined_super_attack:
                lines = [
                    "You wrote super_attack(), but the program never called it.",
                    "Add this line at the bottom of your code:  super_attack()",
                ]
            else:
                lines = [
                    "Your program did not fire a super attack.",
                    "Define and call super_attack(), and use fire_super_attack() inside it.",
                ]
            self.notice = Notice("info", "The boss is still standing", lines)
            return
        if self.coins < C.SUPER_ATTACK_COST:
            self.notice = Notice(
                "failure",
                "Not enough coins",
                [
                    f"The super attack needs {C.SUPER_ATTACK_COST} coins.",
                    f"You have {self.coins}.",
                    "Go back to Escape the Maze and collect more supplies.",
                ],
            )
            self._sound("fail")
            return
        self.notice = Notice(
            "info",
            "The boss survived",
            ["Check the if-else inside super_attack().",
             f"With {self.coins} coins the attack should work."],
        )

    # ------------------------------------------------------------ helpers
    def _sound(self, name: str) -> None:
        self.sounds.append(name)

    @property
    def running(self) -> bool:
        return self.run_state == C.RUN_RUNNING

    def progress_label(self) -> str:
        done = sum([self.has_character, self.maze_done, self.boss_done])
        return f"{done} of 3 missions complete"

    @property
    def current_spec(self) -> mission_one.LevelSpec:
        index = max(0, min(len(self.level_specs) - 1, self.level_index))
        return self.level_specs[index]

    @property
    def level_count(self) -> int:
        return len(self.levels)

    def current_level_name(self) -> str:
        return self.current_spec.name

    def level_label(self) -> str:
        spec = self.current_spec
        return f"Level {spec.number} of {len(self.level_specs)}: {spec.name}"

    def current_objective(self) -> str:
        if self.stage == C.STAGE_CREATE:
            return mission_one.OBJECTIVE_CREATE
        if self.stage == C.STAGE_BOSS:
            return mission_one.OBJECTIVE_BOSS
        return self.current_spec.objective

    def current_hints(self) -> tuple[str, ...]:
        if self.stage == C.STAGE_CREATE:
            return mission_one.HINTS_CREATE
        if self.stage == C.STAGE_BOSS:
            return mission_one.HINTS_BOSS
        return self.current_spec.hints

    def current_reference_path(self) -> list[tuple[int, int]] | None:
        """Cells of the teacher route for the current level (None if custom)."""
        if self.custom_maze or self.stage == C.STAGE_BOSS:
            return None
        try:
            return mission_one.reference_path(self.maze, self.current_spec)
        except ValueError:
            return None

    def score(self) -> int:
        return self.coins * 2 + self.weapon_power * 10


def mission_one_objective_title(stage: int) -> str:
    return f"Mission {stage}: {C.STAGE_TITLES[stage]}"
