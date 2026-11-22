"""Modal dialogs: the input() prompt, help overlay and mission notices."""

from __future__ import annotations

import pygame

from engine import constants as C
from education.starter_code import HELP_LINES
from ui.theme import Fonts, draw_text, wrap_text
from ui.widgets import Button, draw_dialog_frame


def dim(surface: pygame.Surface, alpha: int = 170) -> None:
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((4, 6, 14, alpha))
    surface.blit(shade, (0, 0))


def _emblem(surface, centre, kind: str, fonts: Fonts) -> None:
    cx, cy = centre
    colour = {"success": C.COL_GREEN, "failure": C.COL_RED, "error": C.COL_ORANGE}.get(
        kind, C.COL_CYAN
    )
    pygame.draw.circle(surface, (10, 14, 28), (cx, cy), 26)
    pygame.draw.circle(surface, colour, (cx, cy), 24, 3)
    if kind == "success":
        pygame.draw.lines(surface, colour, False, [(cx - 10, cy + 1), (cx - 3, cy + 9), (cx + 11, cy - 8)], 4)
    elif kind == "failure":
        pygame.draw.line(surface, colour, (cx - 9, cy - 9), (cx + 9, cy + 9), 4)
        pygame.draw.line(surface, colour, (cx + 9, cy - 9), (cx - 9, cy + 9), 4)
    else:
        pygame.draw.rect(surface, colour, (cx - 2, cy - 10, 4, 4))
        pygame.draw.rect(surface, colour, (cx - 2, cy - 3, 4, 13))


class InputModal:
    def __init__(self, prompt: str, fonts: Fonts) -> None:
        self.prompt = prompt or "Type your answer:"
        self.text = ""
        self.fonts = fonts
        self.rect = pygame.Rect(0, 0, 640, 300)
        self.buttons: list[Button] = []
        self.caret_time = 0.0
        self.scroll = 0

    def layout(self, width: int, height: int) -> None:
        self.rect.center = (width // 2, height // 2)
        send = Button(pygame.Rect(0, 0, 170, 46), "Send  (Enter)", "primary", action="submit")
        stop = Button(pygame.Rect(0, 0, 150, 46), "Stop program", "secondary", action="cancel")
        send.rect.bottomright = (self.rect.right - 28, self.rect.bottom - 24)
        stop.rect.bottomleft = (self.rect.x + 28, self.rect.bottom - 24)
        self.buttons = [send, stop]

    def _input_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.x + 28, self.rect.y + 176, self.rect.width - 56, 48)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.TEXTINPUT:
            self.text += event.text
            self.caret_time = 0.0
            return None
        if event.type == pygame.KEYDOWN:
            self.caret_time = 0.0
            if event.key == pygame.K_RETURN:
                return "submit"
            if event.key == pygame.K_ESCAPE:
                return "cancel"
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    return button.action
        return None

    def draw(self, surface, now: float) -> None:
        dim(surface)
        fonts = self.fonts
        draw_dialog_frame(surface, self.rect, fonts, "THE GAME IS ASKING FOR INPUT", C.COL_CYAN)
        prompt_lines = wrap_text(fonts.body(19), self.prompt, self.rect.width - 60)
        y = self.rect.y + 66
        for line in prompt_lines[:3]:
            draw_text(surface, line, fonts.body(19), C.COL_TEXT, (self.rect.x + 28, y))
            y += 26
        box = self._input_rect()
        pygame.draw.rect(surface, (8, 10, 24), box)
        pygame.draw.rect(surface, C.COL_CYAN, box, 2)
        font = fonts.code(24)
        # keep the caret visible inside the box
        caret_x = font.size(self.text)[0]
        available = box.width - 30
        while caret_x - self.scroll > available:
            self.scroll += max(1, caret_x - self.scroll - available)
        self.scroll = max(0, min(self.scroll, max(0, caret_x - available)))
        old_clip = surface.get_clip()
        surface.set_clip(box.inflate(-6, -6))
        draw_text(surface, self.text, font, C.COL_TEXT, (box.x + 12 - self.scroll, box.centery), align="midleft")
        if (now - self.caret_time) % 1.0 < 0.55:
            cx = box.x + 12 + caret_x - self.scroll
            pygame.draw.rect(surface, C.COL_CYAN, (cx, box.y + 10, 2, box.height - 20))
        surface.set_clip(old_clip)
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, fonts, mouse)
        draw_text(surface, "Enter sends your answer. Esc stops the program.",
                  fonts.body(12), C.COL_TEXT_FAINT, (self.rect.centerx, self.rect.y + 136), align="center")


class NoticeModal:
    def __init__(self, notice, fonts: Fonts) -> None:
        self.notice = notice
        self.fonts = fonts
        self.rect = pygame.Rect(0, 0, 660, 400)
        self.buttons: list[Button] = []
        if notice.kind == "error":
            primary = Button(pygame.Rect(0, 0, 190, 46), "Fix my code", "primary", action="close")
        elif notice.kind == "failure":
            primary = Button(pygame.Rect(0, 0, 190, 46), "Restart mission", "primary", action="retry")
        elif notice.action == "next_stage":
            primary = Button(pygame.Rect(0, 0, 190, 46), "Next mission", "primary", action="next")
        elif notice.action == "next_level":
            primary = Button(pygame.Rect(0, 0, 190, 46), "Next level", "primary", action="next_level")
        else:
            primary = Button(pygame.Rect(0, 0, 190, 46), "Continue", "primary", action="close")
        secondary = Button(pygame.Rect(0, 0, 150, 46), "Close", "secondary", action="close")
        self.buttons = [primary, secondary]
        self.primary_action = primary.action

    def layout(self, width: int, height: int) -> None:
        self.rect.center = (width // 2, height // 2)
        first, second = self.buttons
        first.rect.bottomleft = (self.rect.centerx - first.rect.width - 8, self.rect.bottom - 24)
        second.rect.bottomleft = (self.rect.centerx + 8, self.rect.bottom - 24)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.primary_action
            if event.key == pygame.K_ESCAPE:
                return "close"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    return button.action
        return None

    def draw(self, surface, now: float) -> None:
        dim(surface)
        fonts = self.fonts
        notice = self.notice
        title = notice.title.upper()
        accent = {"success": C.COL_GREEN, "failure": C.COL_RED, "error": C.COL_ORANGE}.get(
            notice.kind, C.COL_CYAN
        )
        pygame.draw.rect(surface, (4, 6, 14), self.rect.move(6, 6))
        pygame.draw.rect(surface, C.COL_PANEL, self.rect)
        pygame.draw.rect(surface, accent, self.rect, 3)
        _emblem(surface, (self.rect.centerx, self.rect.y + 58), notice.kind, fonts)
        draw_text(surface, title, fonts.heading(24), accent, (self.rect.centerx, self.rect.y + 100), align="midtop")
        y = self.rect.y + 140
        for raw in notice.lines:
            for line in wrap_text(fonts.body(16), raw, self.rect.width - 72):
                draw_text(surface, line, fonts.body(16), C.COL_TEXT, (self.rect.centerx, y), align="midtop")
                y += 23
            y += 4
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, fonts, mouse)


class HelpModal:
    def __init__(self, fonts: Fonts) -> None:
        self.fonts = fonts
        self.rect = pygame.Rect(0, 0, 760, 600)
        self.scroll = 0
        self.close = Button(pygame.Rect(0, 0, 140, 44), "Close", "secondary", action="close")
        self.entries: list[tuple[str, str, str]] = []
        for group, lines in HELP_LINES:
            self.entries.append(("group", group, ""))
            for line in lines:
                name, _, description = line.partition("  ")
                self.entries.append(("line", name.strip(), description.strip()))

    def layout(self, width: int, height: int) -> None:
        self.rect.center = (width // 2, height // 2)
        self.close.rect.bottomright = (self.rect.right - 24, self.rect.bottom - 20)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_F1):
            return "close"
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.max_scroll(), self.scroll - event.y * 30))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close.rect.collidepoint(event.pos):
                return "close"
        return None

    def content_height(self) -> int:
        height = 0
        for kind, _, _ in self.entries:
            height += 34 if kind == "group" else 22
        return height

    def max_scroll(self) -> int:
        return max(0, self.content_height() - (self.rect.height - 120))

    def draw(self, surface, now: float) -> None:
        dim(surface, 190)
        fonts = self.fonts
        inner = draw_dialog_frame(surface, self.rect, fonts, "HELP  ·  GAME AND PYTHON REFERENCE", C.COL_GOLD)
        draw_text(surface, "F1 or Esc closes this window", fonts.body(12), C.COL_TEXT_FAINT,
                  (self.rect.right - 24, self.rect.y + 52), align="topright")
        old_clip = surface.get_clip()
        body = pygame.Rect(inner.x, inner.y + 14, inner.width, self.rect.height - 120)
        surface.set_clip(body)
        y = body.y + 10 - self.scroll
        for kind, name, description in self.entries:
            if kind == "group":
                y += 8
                draw_text(surface, name.upper(), fonts.body(12, bold=True), C.COL_GOLD, (body.x + 16, y))
                pygame.draw.rect(surface, (48, 58, 100), (body.x + 16, y + 18, body.width - 32, 1))
                y += 26
            else:
                draw_text(surface, name, fonts.code(15), C.COL_CYAN, (body.x + 24, y))
                draw_text(surface, description, fonts.body(14), C.COL_TEXT_DIM, (body.x + 260, y + 3))
                y += 22
        surface.set_clip(old_clip)
        if self.max_scroll() > 0:
            draw_text(surface, "scroll to see more", fonts.body(11), C.COL_TEXT_FAINT,
                      (body.centerx, body.bottom - 4), align="midbottom")
        self.close.draw(surface, fonts, pygame.mouse.get_pos())


class HintModal:
    """Progressive hints: one idea at a time, never the full answer code."""

    def __init__(self, hints, fonts: Fonts, start: int = 0, allow_route: bool = False) -> None:
        self.hints = list(hints) or ("No hints for this mission yet.",)
        self.fonts = fonts
        self.step = max(0, min(len(self.hints) - 1, start))
        self.allow_route = allow_route
        self.rect = pygame.Rect(0, 0, 680, 380)
        self.buttons: list[Button] = []
        self._build_buttons()

    # -------------------------------------------------------------- content
    @property
    def last(self) -> bool:
        return self.step >= len(self.hints) - 1

    def advance(self) -> bool:
        if self.last:
            return False
        self.step += 1
        self._build_buttons()
        self._place_buttons()
        return True

    def _build_buttons(self) -> None:
        buttons: list[Button] = []
        if self.last:
            buttons.append(Button(pygame.Rect(0, 0, 170, 46), "Got it", "primary", action="close"))
        else:
            buttons.append(Button(pygame.Rect(0, 0, 190, 46), "Next hint", "primary", action="hint_next"))
        if self.allow_route and self.last:
            buttons.append(Button(pygame.Rect(0, 0, 210, 46), "Show route on map", "secondary", action="hint_route"))
        buttons.append(Button(pygame.Rect(0, 0, 140, 46), "Close", "ghost", action="close"))
        self.buttons = buttons

    def layout(self, width: int, height: int) -> None:
        self.rect.center = (width // 2, height // 2)
        self._place_buttons()

    def _place_buttons(self) -> None:
        gap = 12
        total = sum(b.rect.width for b in self.buttons) + gap * (len(self.buttons) - 1)
        x = self.rect.centerx - total // 2
        for button in self.buttons:
            button.rect.bottomleft = (x, self.rect.bottom - 24)
            x += button.rect.width + gap

    # --------------------------------------------------------------- events
    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return "close" if self.last else "hint_next"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    return button.action
        return None

    # ----------------------------------------------------------------- draw
    def draw(self, surface, now: float) -> None:
        dim(surface)
        fonts = self.fonts
        draw_dialog_frame(surface, self.rect, fonts, "HINT  -  BUILD IT UP STEP BY STEP", C.COL_GOLD)
        draw_text(
            surface,
            f"HINT {self.step + 1} / {len(self.hints)}",
            fonts.heading(24),
            C.COL_GOLD,
            (self.rect.centerx, self.rect.y + 78),
            align="midtop",
        )
        y = self.rect.y + 124
        for line in wrap_text(fonts.body(20), self.hints[self.step], self.rect.width - 96):
            draw_text(surface, line, fonts.body(20), C.COL_TEXT, (self.rect.centerx, y), align="midtop")
            y += 28
        dot_y = self.rect.y + 236
        spacing = 22
        start_x = self.rect.centerx - (len(self.hints) - 1) * spacing // 2
        for index in range(len(self.hints)):
            colour = C.COL_GOLD if index <= self.step else (52, 62, 104)
            pygame.draw.circle(surface, colour, (start_x + index * spacing, dot_y), 6)
        footer = "Each hint adds one idea. Try the code after every hint."
        if self.allow_route and self.last:
            footer = "Still stuck? Reveal the reference route on the map."
        draw_text(surface, footer, fonts.body(13), C.COL_TEXT_FAINT,
                  (self.rect.centerx, self.rect.y + 262), align="midtop")
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(surface, fonts, mouse)
