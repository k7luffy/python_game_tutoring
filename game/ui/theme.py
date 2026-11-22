"""Colours, fonts and small drawing helpers for the pixel-styled UI."""

from __future__ import annotations

import pygame

from engine import constants as C

FONT_HEADING = ["arialblack", "impact", "arial", "verdana", "dejavusans"]
FONT_BODY = ["verdana", "arial", "helveticaneue", "dejavusans"]
FONT_CODE = ["menlo", "consolas", "dejavusansmono", "couriernew", "monaco"]


class Fonts:
    """Cached font lookup with sensible cross-platform fallbacks."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, int, bool], pygame.font.Font] = {}
        self.heading_path = self._find(FONT_HEADING, monospace=False)
        self.body_path = self._find(FONT_BODY, monospace=False)
        self.code_path = self._find(FONT_CODE, monospace=True)

    @staticmethod
    def _find(names: list[str], monospace: bool) -> str | None:
        for name in names:
            path = pygame.font.match_font(name)
            if not path:
                continue
            if monospace:
                try:
                    probe = pygame.font.Font(path, 20)
                    if probe.size("M")[0] != probe.size("i")[0]:
                        continue
                except Exception:
                    continue
            return path
        return None

    def _get(self, path: str | None, size: int, bold: bool = False) -> pygame.font.Font:
        key = (path or "", size, bold)
        font = self._cache.get(key)
        if font is None:
            if path:
                font = pygame.font.Font(path, size)
            else:
                font = pygame.font.SysFont("arial", size, bold=bold)
            font.set_bold(bold)
            self._cache[key] = font
        return font

    def heading(self, size: int) -> pygame.font.Font:
        return self._get(self.heading_path, size, bold=True)

    def body(self, size: int, bold: bool = False) -> pygame.font.Font:
        return self._get(self.body_path, size, bold=bold)

    def code(self, size: int) -> pygame.font.Font:
        return self._get(self.code_path, size)


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    colour,
    pos,
    *,
    shadow=None,
    shadow_offset: int = 2,
    align: str = "topleft",
    alpha: int = 255,
) -> pygame.Rect:
    image = font.render(text, True, colour)
    if alpha != 255:
        image = image.copy()
        image.set_alpha(alpha)
    rect = image.get_rect(**{align: pos})
    if shadow is not None:
        shade = font.render(text, True, shadow)
        if alpha != 255:
            shade.set_alpha(alpha)
        surface.blit(shade, (rect.x + shadow_offset, rect.y + shadow_offset))
    surface.blit(image, rect)
    return rect


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill=C.COL_PANEL,
    edge=C.COL_PANEL_EDGE,
    radius: int = 0,
    shadow: bool = True,
) -> None:
    if shadow:
        shadow_rect = rect.move(4, 4)
        pygame.draw.rect(surface, (6, 8, 18), shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, edge, rect, width=2, border_radius=radius)
    if rect.width > 6 and rect.height > 6:
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(surface, (0, 0, 0, 0), inner, width=1, border_radius=radius)
        pygame.draw.rect(
            surface,
            tuple(min(255, c + 8) for c in edge),
            inner,
            width=1,
            border_radius=radius,
        )


def pixel_line(surface: pygame.Surface, rect: pygame.Rect, colour) -> None:
    pygame.draw.rect(surface, colour, rect)


def wrap_text(font: pygame.font.Font, text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def vertical_gradient(surface: pygame.Surface, rect: pygame.Rect, top, bottom) -> None:
    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        colour = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(surface, colour, (rect.x, rect.y + y), (rect.right, rect.y + y))


def fit_font(fonts: Fonts, text: str, max_width: int, sizes: list[int], make=None):
    """Return the largest font from sizes that fits the text."""
    make = make or fonts.body
    chosen = make(sizes[-1])
    for size in sizes:
        candidate = make(size)
        if candidate.size(text)[0] <= max_width:
            chosen = candidate
            break
    return chosen
