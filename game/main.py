"""Python Maze Adventure - entry point and application shell.

Run from the repository root with:
    python game/main.py
"""

from __future__ import annotations

import os
import sys
import time

# Keep the window sharp when Windows display scaling is above 100%, and hide
# pygame's support banner.  SDL ignores both hints on macOS and Linux, so they
# must be set before pygame is imported.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
os.environ.setdefault("SDL_WINDOWS_DPI_SCALING", "0")

import pygame

if __package__ in (None, ""):
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from engine import constants as C
from engine.session import Session
from education.starter_code import COMMANDS_BY_STAGE, EDITOR_PLACEHOLDER, STARTER_CODE
from missions import mission_one
from ui.arena import ArenaView
from ui.console import ConsoleView
from ui.editor import Document, Editor
from ui.modals import HelpModal, HintModal, InputModal, NoticeModal
from ui.sound import SoundBank
from ui.sprites import SpriteBank
from ui.theme import Fonts, draw_panel, draw_text, vertical_gradient, wrap_text
from ui.widgets import Button, draw_badge

INITIAL_SIZE = (1280, 800)


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.key.set_repeat(420, 35)
        self.fullscreen = False
        self.window = pygame.display.set_mode(INITIAL_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Python Maze Adventure - The Coin Mission")
        icon_path = __import__("pathlib").Path(__file__).resolve().parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                pygame.display.set_icon(pygame.image.load(str(icon_path)))
            except pygame.error:
                pass
        self.canvas = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        self.fonts = Fonts()
        self.sprites = SpriteBank()
        self.sound = SoundBank()
        self.session = Session()
        self.doc = Document()
        self.doc.set_text(STARTER_CODE[1])
        self.editor = Editor(self.doc, self.fonts.code(16))
        self.editor.focused = True
        self.editor.placeholder = EDITOR_PLACEHOLDER[1]
        self.console_view = ConsoleView()
        self.console_view.font = self.fonts.code(14)
        self.arena = ArenaView(self.session, self.sprites, self.fonts)
        self.stage = 1
        self.buffers = dict(STARTER_CODE)
        self.modal = None
        self.last_notice = None
        self.show_route = False
        self.hint_step = 0
        self.running_flag = True
        self.scale = 1.0
        self.offset = (0, 0)
        self.buttons: dict[str, Button] = {}
        self.build_widgets()
        self.apply_layout()
        self.scanlines = self._make_scanlines()

    # ------------------------------------------------------------- widgets
    def build_widgets(self) -> None:
        self.buttons = {
            "stage1": Button(pygame.Rect(0, 0, 128, 48), "1  Create", "secondary", action="stage1"),
            "stage2": Button(pygame.Rect(0, 0, 128, 48), "2  Maze", "secondary", action="stage2"),
            "stage3": Button(pygame.Rect(0, 0, 128, 48), "3  Boss", "secondary", action="stage3"),
            "sound": Button(pygame.Rect(0, 0, 96, 46), "Sound", "secondary", action="sound", icon="sound"),
            "help": Button(pygame.Rect(0, 0, 44, 46), "?", "secondary", action="help", icon="help"),
            "run": Button(pygame.Rect(0, 0, 144, 48), "Run Code", "primary", action="run", icon="play"),
            "reset": Button(pygame.Rect(0, 0, 116, 48), "Reset", "secondary", action="reset", icon="reset"),
            "speed": Button(pygame.Rect(0, 0, 128, 48), "Speed 1x", "secondary", action="speed"),
            "restart": Button(pygame.Rect(0, 0, 126, 48), "Restart all", "ghost", action="restart"),
            "clear": Button(pygame.Rect(0, 0, 96, 48), "Clear", "ghost", action="clear"),
            "hint": Button(pygame.Rect(0, 0, 150, 34), "Hint", "ghost", action="hint"),
        }
        for number in range(1, self.session.level_count + 1):
            self.buttons[f"level{number}"] = Button(
                pygame.Rect(0, 0, 24, 24), str(number), "ghost", action=f"level{number}"
            )

    def apply_layout(self) -> None:
        b = self.buttons
        b["stage1"].rect.topleft = (392, 18)
        b["stage2"].rect.topleft = (528, 18)
        b["stage3"].rect.topleft = (664, 18)
        b["sound"].rect.topleft = (1264, 20)
        b["help"].rect.topleft = (1368, 20)
        b["run"].rect.topleft = (768, 108)
        b["reset"].rect.topleft = (920, 108)
        b["speed"].rect.topleft = (1044, 108)
        b["restart"].rect.topleft = (1180, 108)
        b["clear"].rect.topleft = (1314, 108)
        b["hint"].rect.topright = (708, 116)
        for number in range(1, self.session.level_count + 1):
            b[f"level{number}"].rect = pygame.Rect(430 + (number - 1) * 24, 120, 24, 24)
        self.left_panel = pygame.Rect(20, 96, 724, 788)
        self.right_panel = pygame.Rect(756, 96, 664, 788)
        self.maze_rect = pygame.Rect(32, 160, 700, 468)
        self.objective_rect = pygame.Rect(32, 640, 700, 112)
        self.legend_rect = pygame.Rect(32, 760, 700, 76)
        self.status_rect = pygame.Rect(32, 844, 700, 32)
        self.command_rect = pygame.Rect(768, 164, 640, 84)
        self.boss_bar_rect = pygame.Rect(300, 120, 212, 22)
        self.editor.set_rect(pygame.Rect(768, 256, 640, 344))
        self.console_view.set_rect(pygame.Rect(768, 612, 640, 246))
        self.arena.set_rect(self.maze_rect)
        if self.modal is not None:
            self.modal.layout(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)

    @staticmethod
    def _make_scanlines() -> pygame.Surface:
        surface = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, C.WINDOW_HEIGHT, 3):
            pygame.draw.line(surface, (0, 0, 0, 10), (0, y), (C.WINDOW_WIDTH, y))
        return surface

    # ------------------------------------------------------------ stage flow
    def switch_stage(self, stage: int, force: bool = False) -> None:
        if self.session.running:
            self.session.stop_run(silent=True)
        if not force:
            self.buffers[self.stage] = self.doc.text
        self.stage = stage
        self.session.select_stage(stage)
        self.doc.set_text(self.buffers[stage])
        self.editor.scroll_row = 0
        self.editor.scroll_x = 0
        self.editor.focused = True
        self.editor.placeholder = EDITOR_PLACEHOLDER[stage]
        self.editor.scroll_row = 0
        self.console_view.reset()
        self.arena.set_rect(self.maze_rect)
        self.arena.invalidate()
        self.show_route = False
        self.hint_step = 0
        self.modal = None
        self.last_notice = self.session.notice

    def switch_level(self, index: int) -> None:
        """Jump to one of the four maze levels (level dots / Next level)."""
        if self.session.running:
            self.session.stop_run(silent=True)
        if self.stage != C.STAGE_MAZE:
            self.buffers[self.stage] = self.doc.text
            self.buffers[C.STAGE_MAZE] = self.buffers.get(C.STAGE_MAZE, "")
        self.stage = C.STAGE_MAZE
        self.session.select_level(index)
        self.doc.set_text(self.buffers.get(C.STAGE_MAZE, ""))
        self.editor.scroll_row = 0
        self.editor.scroll_x = 0
        self.editor.focused = True
        self.editor.placeholder = EDITOR_PLACEHOLDER[C.STAGE_MAZE]
        self.console_view.reset()
        self.arena.set_rect(self.maze_rect)
        self.arena.invalidate()
        self.show_route = False
        self.hint_step = 0
        self.modal = None
        self.last_notice = self.session.notice

    def restart_all(self) -> None:
        self.session.reset_all()
        self.buffers = dict(STARTER_CODE)
        self.stage = 1
        self.switch_stage(1, force=True)
        self.sound.play("click")

    def toggle_run(self) -> None:
        if self.session.running:
            self.session.stop_run()
            self.sound.play("click")
            return
        self.buffers[self.stage] = self.doc.text
        self.doc.error_line = None
        self.session.start_run(self.doc.text)
        self.sound.play("click")
        if self.session.notice is not None:
            self.open_notice()

    def open_notice(self) -> None:
        notice = self.session.notice
        if notice is None:
            return
        self.last_notice = notice
        self.modal = NoticeModal(notice, self.fonts)
        self.modal.layout(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)

    # --------------------------------------------------------------- input
    def canvas_pos(self, pos) -> tuple[int, int]:
        scale, (ox, oy) = self.scale, self.offset
        if scale <= 0:
            return pos
        return (int((pos[0] - ox) / scale), int((pos[1] - oy) / scale))

    def handle_event(self, event: pygame.event.Event) -> None:
        canvas_mouse = self.canvas_mouse()
        self.editor.mouse_pos = canvas_mouse
        self.console_view.mouse_pos = canvas_mouse
        if event.type == pygame.QUIT:
            self.running_flag = False
            return
        if event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if self.modal is not None:
            if hasattr(event, "pos") and event.type in (
                pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
            ):
                event = self._remap(event)
            action = self.modal.handle_event(event)
            if action:
                self.modal_action(action)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.open_help()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.session.running:
                self.session.stop_run()
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (
            getattr(event, "mod", 0) & (pygame.KMOD_CTRL | pygame.KMOD_META)
        ):
            self.toggle_run()
            return
        pos = None
        if hasattr(event, "pos") and event.type in (
            pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
        ):
            event = self._remap(event)
            pos = event.pos
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and pos is not None:
            for key, button in self.buttons.items():
                if key.startswith("level") and self.stage != C.STAGE_MAZE:
                    continue
                if button.enabled and button.rect.collidepoint(pos):
                    self.sound.play("click")
                    self.handle_action(button.action)
                    return
        if self.editor.handle_event(event):
            return
        if self.console_view.handle_event(event):
            return
        if event.type == pygame.MOUSEMOTION and pos is not None:
            self.arena.hover = self.arena.hovered_cell(pos)

    def _remap(self, event):
        values = dict(event.dict)
        values["pos"] = self.canvas_pos(event.pos)
        return pygame.event.Event(event.type, values)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(INITIAL_SIZE, pygame.RESIZABLE)

    def open_help(self) -> None:
        self.modal = HelpModal(self.fonts)
        self.modal.layout(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)

    def open_hint(self) -> None:
        hints = self.session.current_hints()
        self.hint_step = max(0, min(len(hints) - 1, self.hint_step))
        self.modal = HintModal(
            hints,
            self.fonts,
            start=self.hint_step,
            allow_route=self.stage == C.STAGE_MAZE,
        )
        self.modal.layout(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)

    def handle_action(self, action: str) -> None:
        if action == "run":
            self.toggle_run()
        elif action == "reset":
            self.session.reset_stage()
            self.arena.set_rect(self.maze_rect)
            self.arena.invalidate()
            self.console_view.reset()
            self.doc.error_line = None
        elif action == "speed":
            self.session.cycle_speed()
            self.buttons["speed"].label = f"Speed {C.SPEED_OPTIONS[self.session.speed_index][1]}"
        elif action == "restart":
            self.restart_all()
        elif action == "clear":
            self.session.console.clear()
            self.console_view.reset()
        elif action == "hint":
            self.open_hint()
        elif action == "sound":
            enabled = self.sound.toggle()
            self.buttons["sound"].label = "Sound" if enabled else "Muted"
        elif action == "help":
            self.open_help()
        elif action.startswith("stage"):
            target = int(action[-1])
            if target != self.stage:
                self.switch_stage(target)
                self.sound.play("click")
        elif action.startswith("level"):
            target = int(action[len("level"):]) - 1
            if target != self.session.level_index or self.stage != C.STAGE_MAZE:
                self.switch_level(target)
            self.sound.play("click")

    def modal_action(self, action: str) -> None:
        modal = self.modal
        if action == "submit" and isinstance(modal, InputModal):
            text = modal.text
            self.modal = None
            self.session.submit_input(text)
            self.sound.play("click")
            self.editor.focused = True
        elif action == "cancel" and isinstance(modal, InputModal):
            self.modal = None
            self.session.cancel_input()
        elif action == "hint_next" and isinstance(modal, HintModal):
            if modal.advance():
                self.hint_step = modal.step
                self.sound.play("click")
        elif action == "hint_route":
            self.modal = None
            self.show_route = True
            self.sound.play("click")
            self.editor.focused = True
        elif action == "next":
            self.session.notice = None
            self.modal = None
            if self.stage < C.STAGE_COUNT:
                self.switch_stage(self.stage + 1)
            self.sound.play("success")
        elif action == "next_level":
            self.session.notice = None
            self.modal = None
            if self.session.advance_level():
                self.doc.set_text(self.buffers.get(C.STAGE_MAZE, ""))
                self.editor.scroll_row = 0
                self.editor.scroll_x = 0
                self.editor.focused = True
                self.editor.placeholder = EDITOR_PLACEHOLDER[C.STAGE_MAZE]
                self.console_view.reset()
                self.arena.set_rect(self.maze_rect)
                self.arena.invalidate()
                self.show_route = False
                self.hint_step = 0
                self.last_notice = self.session.notice
            self.sound.play("success")
        elif action == "retry":
            self.session.notice = None
            self.session.reset_stage()
            self.arena.invalidate()
            self.console_view.reset()
            self.modal = None
            self.editor.focused = True
        elif action == "close":
            self.session.notice = None
            self.modal = None
            self.editor.focused = True

    # ---------------------------------------------------------------- frame
    def sync_modal(self) -> None:
        if self.modal is not None:
            return
        if self.session.waiting_input is not None:
            prompt = ""
            request = self.session.waiting_input
            if isinstance(request.payload, dict):
                prompt = str(request.payload.get("prompt", ""))
            self.modal = InputModal(prompt, self.fonts)
            self.modal.layout(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)
            return
        if self.session.notice is not None and self.session.notice is not self.last_notice:
            self.open_notice()

    def update(self, now: float) -> None:
        self.session.update(now)
        for name in self.session.sounds:
            self.sound.play(name)
        self.session.sounds.clear()
        if self.session.error_card is not None and self.session.error_card.line_number:
            line = self.session.error_card.line_number
            if 1 <= line <= len(self.doc.lines):
                self.doc.error_line = line - 1
        self.sync_modal()
        running = self.session.running
        run_button = self.buttons["run"]
        wanted = "Stop" if running else "Run Code"
        if run_button.label != wanted:
            run_button.label = wanted
            run_button.kind = "danger" if running else "primary"
            run_button.icon = "stop" if running else "play"

    def draw(self, now: float) -> None:
        canvas = self.canvas
        vertical_gradient(canvas, canvas.get_rect(), (16, 20, 42), C.COL_BG)
        self.draw_header(now)
        self.draw_left_panel(now)
        self.draw_right_panel(now)
        canvas.blit(self.scanlines, (0, 0))
        if self.modal is not None:
            self.modal.draw(canvas, now)
        self.present()

    def present(self) -> None:
        width, height = self.window.get_size()
        scale = min(width / C.WINDOW_WIDTH, height / C.WINDOW_HEIGHT)
        draw_w = max(1, int(C.WINDOW_WIDTH * scale))
        draw_h = max(1, int(C.WINDOW_HEIGHT * scale))
        offset = ((width - draw_w) // 2, (height - draw_h) // 2)
        self.scale = scale
        self.offset = offset
        self.window.fill((4, 6, 14))
        if (draw_w, draw_h) == (C.WINDOW_WIDTH, C.WINDOW_HEIGHT):
            scaled = self.canvas
        else:
            scaled = pygame.transform.smoothscale(self.canvas, (draw_w, draw_h))
        self.window.blit(scaled, offset)
        pygame.display.flip()

    # -------------------------------------------------------------- drawing
    def draw_header(self, now: float) -> None:
        canvas = self.canvas
        header = pygame.Rect(0, 0, C.WINDOW_WIDTH, 84)
        pygame.draw.rect(canvas, (18, 23, 46), header)
        pygame.draw.rect(canvas, (40, 50, 92), (0, 82, C.WINDOW_WIDTH, 2))
        pygame.draw.rect(canvas, (10, 12, 26), (0, 84, C.WINDOW_WIDTH, 2))
        sprites = self.sprites.at(40)
        robot = sprites.robot_front[0]
        canvas.blit(robot, robot.get_rect(center=(46, 42)))
        title = self.fonts.heading(18)
        draw_text(canvas, "PYTHON MAZE", title, C.COL_GOLD, (74, 20), shadow=(0, 0, 0), shadow_offset=3)
        width = title.size("PYTHON MAZE ")[0]
        draw_text(canvas, "ADVENTURE", title, C.COL_CYAN, (74 + width, 20), shadow=(0, 0, 0), shadow_offset=3)
        draw_text(canvas, "The Coin Mission  ·  Year 6 Python", self.fonts.body(12),
                  C.COL_TEXT_DIM, (76, 52))
        mouse = self.canvas_mouse()
        active = {1: "stage1", 2: "stage2", 3: "stage3"}[self.stage]
        for key in ("stage1", "stage2", "stage3"):
            button = self.buttons[key]
            button.kind = "primary" if key == active else "secondary"
            button.draw(canvas, self.fonts, mouse, pressed=False)
        draw_badge(canvas, pygame.Rect(804, 20, 136, 46), str(self.session.coins), C.COL_GOLD,
                   self.fonts, icon="coin")
        draw_badge(canvas, pygame.Rect(948, 20, 148, 46), f"Power {self.session.weapon_power}",
                   (189, 147, 249), self.fonts, icon="bolt")
        self._draw_progress(pygame.Rect(1104, 20, 152, 46))
        self.buttons["sound"].draw(canvas, self.fonts, mouse)
        self.buttons["help"].draw(canvas, self.fonts, mouse)

    def _draw_progress(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.canvas, (16, 20, 40), rect)
        pygame.draw.rect(self.canvas, (48, 58, 100), rect, 2)
        done = [self.session.has_character, self.session.maze_done, self.session.boss_done]
        for index, flag in enumerate(done):
            box = pygame.Rect(rect.x + 14 + index * 22, rect.y + 16, 14, 14)
            pygame.draw.rect(self.canvas, C.COL_GREEN if flag else (34, 41, 70), box)
            pygame.draw.rect(self.canvas, (60, 72, 120), box, 1)
            if flag:
                pygame.draw.lines(self.canvas, (12, 40, 24), False,
                                  [(box.x + 3, box.y + 7), (box.x + 6, box.y + 10), (box.x + 11, box.y + 4)], 2)
        draw_text(self.canvas, f"{sum(done)}/3", self.fonts.body(12, bold=True),
                  C.COL_TEXT_DIM, (rect.right - 12, rect.centery + 1), align="midright")

    def draw_left_panel(self, now: float) -> None:
        canvas = self.canvas
        draw_panel(canvas, self.left_panel)
        pygame.draw.rect(canvas, (40, 50, 90), (self.left_panel.x + 2, 150, self.left_panel.width - 4, 1))
        draw_text(canvas, f"MISSION {self.stage}", self.fonts.body(11, bold=True),
                  C.COL_TEXT_FAINT, (32, 108))
        draw_text(canvas, C.STAGE_TITLES[self.stage].upper(), self.fonts.heading(18), C.COL_TEXT,
                  (32, 122))
        if self.stage == C.STAGE_BOSS:
            self._draw_boss_bar(self.boss_bar_rect)
        if self.stage == C.STAGE_MAZE:
            self._draw_level_dots()
        self.buttons["hint"].draw(canvas, self.fonts, self.canvas_mouse())
        pygame.draw.rect(canvas, (8, 10, 22), self.maze_rect.inflate(8, 8))
        pygame.draw.rect(canvas, (58, 70, 120), self.maze_rect.inflate(8, 8), 2)
        self.arena.draw(canvas, now, self.show_route)
        self._draw_objective()
        self._draw_legend()
        self._draw_status()

    def _draw_level_dots(self) -> None:
        session = self.session
        draw_text(self.canvas, "LEVEL", self.fonts.body(9, bold=True), C.COL_TEXT_FAINT,
                  (430, 107))
        mouse = self.canvas_mouse()
        for index in range(session.level_count):
            button = self.buttons.get(f"level{index + 1}")
            if button is None:
                continue
            if index == session.level_index:
                button.kind = "primary"
            elif index in session.levels_done:
                button.kind = "success"
            else:
                button.kind = "ghost"
            button.draw(self.canvas, self.fonts, mouse)

    def _draw_boss_bar(self, rect: pygame.Rect) -> None:
        draw_text(self.canvas, "BOSS", self.fonts.body(11, bold=True), C.COL_RED, (rect.x, rect.y - 14))
        pygame.draw.rect(self.canvas, (14, 10, 24), rect)
        pygame.draw.rect(self.canvas, (90, 40, 60), rect, 2)
        inner = rect.inflate(-8, -8)
        fraction = max(0.0, self.session.boss_hp / 100)
        if fraction > 0:
            pygame.draw.rect(self.canvas, C.COL_RED, (inner.x, inner.y, int(inner.width * fraction), inner.height))
            pygame.draw.rect(self.canvas, (255, 150, 150),
                             (inner.x, inner.y, int(inner.width * fraction), max(2, inner.height // 3)))
        draw_text(self.canvas, f"{self.session.boss_hp}%", self.fonts.body(10, bold=True), C.COL_TEXT,
                  rect.center, align="center")

    def _draw_objective(self) -> None:
        rect = self.objective_rect
        pygame.draw.rect(self.canvas, (30, 37, 68), rect)
        pygame.draw.rect(self.canvas, (58, 70, 120), rect, 2)
        pygame.draw.rect(self.canvas, C.COL_GOLD, (rect.x, rect.y, 5, rect.height))
        draw_text(self.canvas, "MISSION BRIEF", self.fonts.body(10, bold=True), C.COL_GOLD,
                  (rect.x + 16, rect.y + 10))
        objective = self.session.current_objective()
        tips = {1: mission_one.TIPS_CREATE, 2: mission_one.TIPS_MAZE, 3: mission_one.TIPS_BOSS}
        y = rect.y + 28
        for line in wrap_text(self.fonts.body(14), objective, rect.width - 32):
            draw_text(self.canvas, line, self.fonts.body(14), C.COL_TEXT, (rect.x + 16, y))
            y += 20
        tip = tips[self.stage][0]
        for line in wrap_text(self.fonts.body(12), f"TIP  {tip}", rect.width - 32)[:1]:
            draw_text(self.canvas, line, self.fonts.body(12), C.COL_ORANGE, (rect.x + 16, rect.bottom - 22))

    def _draw_legend(self) -> None:
        rect = self.legend_rect
        pygame.draw.rect(self.canvas, (22, 28, 52), rect)
        pygame.draw.rect(self.canvas, (48, 58, 100), rect, 2)
        sprites = self.sprites.at(32)
        if self.session.stage == C.STAGE_BOSS:
            draw_text(self.canvas, "BOSS ARENA", self.fonts.body(10, bold=True),
                      C.COL_TEXT_FAINT, (rect.x + 12, rect.y + 8))
            draw_text(self.canvas, "Every move: -1 coin", self.fonts.body(13, bold=True),
                      C.COL_ORANGE, (rect.x + 12, rect.y + 30))
            draw_text(self.canvas, "Attack pad: cyan tile", self.fonts.body(13),
                      C.COL_CYAN, (rect.x + 230, rect.y + 30))
            draw_text(self.canvas, "Fire inside if coins >= 30:", self.fonts.body(13),
                      C.COL_GREEN, (rect.x + 440, rect.y + 30))
            draw_text(self.canvas, "The boss blocks its own tile - walk around it.",
                      self.fonts.body(11), C.COL_TEXT_DIM, (rect.x + 12, rect.y + 54))
            return
        draw_text(self.canvas, "SUPPLIES", self.fonts.body(10, bold=True), C.COL_TEXT_FAINT,
                  (rect.x + 12, rect.y + 8))
        coin = sprites.coin[0]
        self.canvas.blit(coin, (rect.x + 12, rect.y + 24))
        draw_text(self.canvas, "Gold coin  +10", self.fonts.body(13), C.COL_TEXT, (rect.x + 38, rect.y + 30))
        chest = sprites.chest_closed
        self.canvas.blit(chest, (rect.x + 180, rect.y + 24))
        draw_text(self.canvas, "Chest  +20", self.fonts.body(13), C.COL_TEXT, (rect.x + 206, rect.y + 30))
        draw_text(self.canvas, "Every step: -1 coin", self.fonts.body(13, bold=True), C.COL_ORANGE,
                  (rect.x + 344, rect.y + 30))
        draw_text(self.canvas, "Reach the base to pass", self.fonts.body(13), C.COL_GREEN,
                  (rect.x + 540, rect.y + 30))
        draw_text(self.canvas, f"Supplies left: {len(self.session.supplies_left)}",
                  self.fonts.body(11), C.COL_TEXT_DIM, (rect.x + 12, rect.y + 54))

    def _draw_status(self) -> None:
        session = self.session
        rect = self.status_rect
        if session.stage == C.STAGE_CREATE:
            text = (f"Name: {session.player_name}    Weapon power: {session.weapon_power}    "
                    f"Coins: {session.coins}")
        elif session.stage == C.STAGE_MAZE:
            spec = session.current_spec
            text = (f"Level {session.level_index + 1}/{session.level_count}  ·  "
                    f"Steps: {session.steps}    Coins: {session.coins} / {spec.start_coins}    "
                    f"Supplies: {len(session.supplies_left)}")
        else:
            tag = "practice run" if session.practice_run else "checkpoint coins"
            pad = session.maze.goal
            on_pad = pad is not None and (session.player.x, session.player.y) == pad
            text = (f"Coins: {session.coins} ({tag})    Attack needs: {C.SUPER_ATTACK_COST}    "
                    f"Pad: {'reached' if on_pad else 'not yet'}    Steps: {session.steps}")
        draw_text(self.canvas, text, self.fonts.body(13), C.COL_TEXT_DIM, (rect.x + 2, rect.y + 8))

    def draw_right_panel(self, now: float) -> None:
        canvas = self.canvas
        draw_panel(canvas, self.right_panel)
        mouse = self.canvas_mouse()
        for key in ("run", "reset", "speed", "restart", "clear"):
            self.buttons[key].draw(canvas, self.fonts, mouse)
        self._draw_commands()
        self.editor.draw(canvas, now)
        self.console_view.draw(canvas, self.fonts, self.session.console, now)
        draw_text(canvas, "Ctrl+Enter run  ·  Esc stop  ·  F1 help  ·  Tab indents",
                  self.fonts.body(11), C.COL_TEXT_FAINT, (self.right_panel.centerx, 868), align="midtop")

    def _draw_commands(self) -> None:
        rect = self.command_rect
        pygame.draw.rect(self.canvas, (26, 33, 62), rect)
        pygame.draw.rect(self.canvas, (52, 64, 116), rect, 2)
        draw_text(self.canvas, "COMMANDS YOU CAN USE", self.fonts.body(10, bold=True),
                  C.COL_CYAN, (rect.x + 14, rect.y + 7))
        draw_text(self.canvas, C.STAGE_TITLES[self.stage], self.fonts.body(10),
                  C.COL_TEXT_FAINT, (rect.right - 14, rect.y + 7), align="topright")
        items = COMMANDS_BY_STAGE.get(self.stage, [])
        for index, (code, note) in enumerate(items):
            row, col = divmod(index, 2)
            x = rect.x + 16 + col * 308
            y = rect.y + 28 + row * 19
            draw_text(self.canvas, code, self.fonts.code(12), C.COL_GOLD, (x, y))
            width = self.fonts.code(12).size(code)[0]
            draw_text(self.canvas, note, self.fonts.body(11), C.COL_TEXT_DIM, (x + width + 8, y + 2))

    def canvas_mouse(self) -> tuple[int, int]:
        return self.canvas_pos(pygame.mouse.get_pos())

    # ----------------------------------------------------------------- loop
    def run(self) -> None:
        self.running_flag = True
        clock = pygame.time.Clock()
        while self.running_flag:
            now = time.monotonic()
            for event in pygame.event.get():
                self.handle_event(event)
                if not self.running_flag:
                    break
            self.update(now)
            self.draw(now)
            clock.tick(C.TARGET_FPS)
        pygame.quit()


def _ensure_utf8_console() -> None:
    """Never let a legacy Windows code page stop the game from opening.

    A Windows console defaults to cp1252 (or another legacy code page), where
    printing a character such as the middle dot raises UnicodeEncodeError.
    Reconfiguring the streams keeps any startup message printable.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main() -> None:
    _ensure_utf8_console()
    App().run()


if __name__ == "__main__":
    main()
