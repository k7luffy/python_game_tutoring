"""Colour-coded transcript panel for the student's print() output."""

from __future__ import annotations

import pygame

from engine import constants as C
from ui.theme import Fonts, draw_text

KIND_COLOURS = {
    "student": C.COL_TEXT,
    "game": C.COL_TEXT_DIM,
    "system": (128, 142, 184),
    "ok": C.COL_GREEN,
    "warn": C.COL_ORANGE,
    "error": C.COL_RED,
}
KIND_BARS = {
    "ok": C.COL_GREEN,
    "error": C.COL_RED,
    "warn": C.COL_ORANGE,
    "system": (58, 72, 118),
    "student": (36, 44, 78),
    "game": (36, 44, 78),
}


def wrap_line(font: pygame.font.Font, text: str, width: int) -> list[str]:
    if not text:
        return [""]
    if font.size(text)[0] <= width:
        return [text]
    chunks: list[str] = []
    current = ""
    for word in text.split(" "):
        trial = f"{current} {word}" if current else word
        if font.size(trial)[0] <= width:
            current = trial
            continue
        if current:
            chunks.append(current)
        while font.size(word)[0] > width and len(word) > 1:
            cut = len(word)
            while cut > 1 and font.size(word[:cut])[0] > width:
                cut -= 1
            chunks.append(word[:cut])
            word = word[cut:]
        current = word
    chunks.append(current)
    return chunks


class ConsoleView:
    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.font: pygame.font.Font | None = None
        self.scroll = 0
        self._cache_key = None
        self._wrapped: list[tuple[str, str, bool]] = []
        self.mouse_pos = (0, 0)
        self.header_height = 34

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def reset(self) -> None:
        self.scroll = 0

    def _wrap(self, console, font: pygame.font.Font, width: int) -> None:
        entries = console.snapshot()
        key = (len(entries), width, entries[-1].text if entries else "")
        if key == self._cache_key:
            return
        self._cache_key = key
        wrapped: list[tuple[str, str, bool]] = []
        for entry in entries:
            chunks = wrap_line(font, entry.text, max(40, width))
            for index, chunk in enumerate(chunks):
                wrapped.append((chunk, entry.kind, index == 0))
        self._wrapped = wrapped

    def visible_count(self) -> int:
        if self.font is None:
            return 1
        height = self.rect.height - self.header_height - 16
        return max(1, height // (self.font.get_linesize() + 2))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(self.mouse_pos):
            total = len(self._wrapped)
            limit = max(0, total - self.visible_count())
            self.scroll = max(0, min(limit, self.scroll + event.y * 3))
            return True
        return False

    def draw(self, surface: pygame.Surface, fonts: Fonts, console, now: float) -> None:
        rect = self.rect
        pygame.draw.rect(surface, C.COL_BG_DEEP, rect)
        pygame.draw.rect(surface, C.COL_PANEL_EDGE, rect, 2)
        header = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, self.header_height)
        pygame.draw.rect(surface, (18, 23, 44), header)
        pygame.draw.line(surface, (40, 48, 84), header.bottomleft, header.bottomright)
        draw_text(surface, "OUTPUT", fonts.body(11, bold=True), C.COL_TEXT_FAINT,
                  (header.x + 12, header.centery), align="midleft")
        count = len(self._wrapped)
        if count:
            draw_text(surface, f"{count} lines", fonts.body(11), C.COL_TEXT_FAINT,
                      (header.right - 12, header.centery), align="midright")

        font = self.font or fonts.code(14)
        self.font = font
        inner_width = rect.width - 34
        self._wrap(console, font, inner_width)
        rows = self.visible_count()
        total = len(self._wrapped)
        limit = max(0, total - rows)
        self.scroll = min(self.scroll, limit)
        start = max(0, total - rows - self.scroll)
        y = header.bottom + 6
        line_h = font.get_linesize() + 2
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(rect.x + 2, header.bottom, rect.width - 4, rect.height - self.header_height - 3))
        for text, kind, first in self._wrapped[start:start + rows]:
            colour = KIND_COLOURS.get(kind, C.COL_TEXT)
            if first:
                pygame.draw.rect(surface, KIND_BARS.get(kind, (36, 44, 78)), (rect.x + 8, y + 3, 3, line_h - 6))
            surface.blit(font.render(text, True, colour), (rect.x + 18, y))
            y += line_h
        if total == 0:
            draw_text(surface, "Your print() output and game messages appear here.",
                      fonts.body(13), C.COL_TEXT_FAINT, (rect.x + 16, header.bottom + 14))
            draw_text(surface, "Press Run Code to start.",
                      fonts.body(13), C.COL_TEXT_FAINT, (rect.x + 16, header.bottom + 36))
        surface.set_clip(old_clip)
        if total > rows:
            track = pygame.Rect(rect.right - 9, header.bottom + 4, 4, rect.height - self.header_height - 10)
            pygame.draw.rect(surface, (18, 22, 42), track)
            height = max(20, int(track.height * rows / total))
            max_scroll = max(1, total - rows)
            position = int((track.height - height) * (1 - self.scroll / max_scroll))
            pygame.draw.rect(surface, (70, 84, 132), (track.x, track.y + position, track.width, height))
            if self.scroll:
                draw_text(surface, "up", fonts.body(10), C.COL_GOLD,
                          (track.centerx, track.y - 2), align="midbottom")
