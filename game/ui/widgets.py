"""Small pixel-styled UI widgets drawn straight onto the logical surface."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from engine import constants as C
from ui.theme import Fonts, draw_text, wrap_text

BUTTON_STYLES = {
    #        face            shadow          edge            text
    "primary": ((255, 205, 74), (170, 116, 12), (255, 236, 150), (32, 24, 6)),
    "secondary": ((44, 54, 96), (16, 20, 40), (78, 94, 160), C.COL_TEXT),
    "danger": ((214, 72, 86), (128, 28, 44), (255, 140, 150), (255, 240, 240)),
    "success": ((80, 205, 120), (28, 120, 66), (160, 255, 190), (10, 40, 20)),
    "ghost": ((26, 32, 60), (12, 15, 30), (52, 64, 116), C.COL_TEXT_DIM),
}


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    kind: str = "primary"
    enabled: bool = True
    action: str = ""
    icon: str = ""          # "coin" | "play" | "stop" | "reset" | "sound" | "help"

    def hovered(self, mouse) -> bool:
        return self.enabled and self.rect.collidepoint(mouse)

    def draw(self, surface, fonts: Fonts, mouse, pressed: bool = False) -> None:
        face, shadow, edge, text_colour = BUTTON_STYLES.get(
            self.kind, BUTTON_STYLES["secondary"]
        )
        hover = self.hovered(mouse)
        if not self.enabled:
            face = (34, 39, 66)
            shadow = (16, 18, 34)
            edge = (48, 56, 92)
            text_colour = (96, 106, 142)
        elif hover:
            face = tuple(min(255, c + 18) for c in face)
        offset = 2 if pressed and hover else 0
        rect = self.rect.move(0, offset)
        pygame.draw.rect(surface, shadow, rect.move(0, 4))
        pygame.draw.rect(surface, face, rect)
        pygame.draw.rect(surface, edge, rect, width=2)
        pygame.draw.rect(
            surface, tuple(min(255, c + 30) for c in face), (rect.x + 2, rect.y + 2, rect.width - 4, 2)
        )
        pygame.draw.rect(surface, shadow, (rect.x + 2, rect.bottom - 3, rect.width - 4, 2))

        font = fonts.body(16, bold=True)
        label = self.label
        icon_w = 0
        if self.icon:
            icon_w = 22
        while font.size(label)[0] + icon_w + 16 > rect.width and label:
            label = label[:-1]
        total = font.size(label)[0] + icon_w
        x = rect.centerx - total // 2
        if self.icon:
            self._draw_icon(surface, (x, rect.centery), text_colour)
            x += icon_w
        draw_text(surface, label, font, text_colour, (x, rect.centery), align="midleft")

    def _draw_icon(self, surface, centre, colour) -> None:
        cx, cy = centre
        if self.icon == "play":
            pygame.draw.polygon(
                surface, colour, [(cx - 4, cy - 6), (cx + 6, cy), (cx - 4, cy + 6)]
            )
        elif self.icon == "stop":
            pygame.draw.rect(surface, colour, (cx - 5, cy - 5, 10, 10))
        elif self.icon == "reset":
            pygame.draw.circle(surface, colour, (cx, cy), 6, 2)
            pygame.draw.polygon(surface, colour, [(cx + 2, cy - 9), (cx + 8, cy - 6), (cx + 3, cy - 2)])
        elif self.icon == "coin":
            pygame.draw.circle(surface, colour, (cx, cy), 6)
            pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 6, 1)
            pygame.draw.circle(surface, C.COL_GOLD_DARK, (cx, cy), 3, 1)
        elif self.icon == "sound":
            pygame.draw.rect(surface, colour, (cx - 7, cy - 3, 4, 6))
            pygame.draw.polygon(
                surface, colour, [(cx - 3, cy - 3), (cx + 2, cy - 7), (cx + 2, cy + 7), (cx - 3, cy + 3)]
            )
            pygame.draw.arc(surface, colour, (cx + 1, cy - 6, 8, 12), -1.0, 1.0, 2)
        elif self.icon == "help":
            draw_text(surface, "?", pygame.font.Font(None, 18), colour, (cx, cy), align="center")


def draw_badge(surface, rect, label, colour, fonts: Fonts, icon: str = "") -> None:
    """A compact stat badge: coloured icon chip plus bold value."""
    body = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
    pygame.draw.rect(surface, (16, 20, 40), body)
    pygame.draw.rect(surface, (48, 58, 100), body, 2)
    chip = pygame.Rect(rect.x + 2, rect.y + 2, 34, rect.height - 4)
    pygame.draw.rect(surface, colour, chip)
    pygame.draw.rect(surface, (10, 12, 24), chip, 1)
    cx, cy = chip.centerx, chip.centery
    if icon == "coin":
        pygame.draw.circle(surface, (70, 44, 8), (cx, cy), 9)
        pygame.draw.circle(surface, C.COL_GOLD, (cx, cy), 8)
        pygame.draw.circle(surface, (255, 244, 190), (cx - 2, cy - 2), 3)
    elif icon == "bolt":
        pygame.draw.polygon(
            surface,
            (30, 20, 8),
            [(cx + 2, cy - 10), (cx - 7, cy + 1), (cx - 1, cy + 1), (cx - 4, cy + 10),
             (cx + 7, cy - 2), (cx + 1, cy - 2)],
        )
    elif icon == "flag":
        pygame.draw.rect(surface, (20, 16, 8), (cx - 8, cy - 9, 3, 19))
        pygame.draw.polygon(surface, (20, 16, 8), [(cx - 5, cy - 9), (cx + 9, cy - 4), (cx - 5, cy + 1)])
        pygame.draw.rect(surface, (240, 240, 230), (cx - 7, cy - 8, 2, 17))
        pygame.draw.polygon(surface, (240, 240, 230), [(cx - 5, cy - 8), (cx + 7, cy - 4), (cx - 5, cy)])
    else:
        draw_text(surface, icon[:1].upper(), fonts.body(14, bold=True), (20, 16, 8),
                  (cx, cy), align="center")
    draw_text(surface, label, fonts.body(15, bold=True), C.COL_TEXT,
              (body.x + 46, body.centery + 1), align="midleft")


def draw_stat(surface, rect, icon, value, caption, colour, fonts: Fonts) -> None:
    pygame.draw.rect(surface, C.COL_BG_DEEP, rect)
    pygame.draw.rect(surface, C.COL_PANEL_EDGE, rect, 2)
    icon_rect = pygame.Rect(rect.x + 8, rect.centery - 12, 24, 24)
    pygame.draw.rect(surface, colour, icon_rect)
    if icon == "coin":
        pygame.draw.circle(surface, (90, 60, 10), icon_rect.center, 8)
        pygame.draw.circle(surface, C.COL_GOLD, icon_rect.center, 7)
        pygame.draw.circle(surface, (255, 244, 190), (icon_rect.centerx - 1, icon_rect.centery - 1), 3)
    elif icon == "bolt":
        cx, cy = icon_rect.center
        pygame.draw.polygon(surface, C.COL_GOLD, [(cx + 2, cy - 9), (cx - 6, cy + 1), (cx - 1, cy + 1),
                                                  (cx - 3, cy + 9), (cx + 6, cy - 2), (cx + 1, cy - 2)])
    elif icon == "flag":
        pygame.draw.rect(surface, C.COL_TEXT_DIM, (cx - 6, cy - 9, 2, 18))
        pygame.draw.polygon(surface, C.COL_MAGENTA, [(cx - 4, cy - 9), (cx + 8, cy - 5), (cx - 4, cy - 1)])
    draw_text(surface, str(value), fonts.heading(22), C.COL_TEXT, (rect.x + 40, rect.y + 6))
    draw_text(surface, caption.upper(), fonts.body(11, bold=True), C.COL_TEXT_FAINT, (rect.x + 40, rect.y + 34))


def draw_progress(surface, rect, fraction, colour, fonts: Fonts, label: str = "") -> None:
    pygame.draw.rect(surface, C.COL_BG_DEEP, rect)
    pygame.draw.rect(surface, C.COL_PANEL_EDGE, rect, 2)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (28, 34, 60), inner)
    fill_w = int(inner.width * max(0.0, min(1.0, fraction)))
    if fill_w > 0:
        pygame.draw.rect(surface, colour, (inner.x, inner.y, fill_w, inner.height))
        pygame.draw.rect(surface, tuple(min(255, c + 40) for c in colour),
                         (inner.x, inner.y, fill_w, max(2, inner.height // 4)))
    if label:
        draw_text(surface, label, fonts.body(12, bold=True), C.COL_TEXT, rect.center, align="center",
                  shadow=(0, 0, 0))


def draw_toggle(surface, rect, on: bool, fonts: Fonts, label: str = "") -> None:
    track = pygame.Rect(rect.x, rect.y, 44, 24)
    pygame.draw.rect(surface, (18, 22, 42) if not on else (30, 90, 70), track)
    pygame.draw.rect(surface, C.COL_PANEL_EDGE, track, 2)
    knob = pygame.Rect(track.right - 20 if on else track.x + 4, track.y + 4, 16, 16)
    pygame.draw.rect(surface, C.COL_GREEN if on else C.COL_TEXT_FAINT, knob)
    if label:
        draw_text(surface, label, fonts.body(14), C.COL_TEXT_DIM,
                  (track.right + 8, track.centery), align="midleft")


def draw_legend_row(surface, x, y, name, value, fonts: Fonts, sprite=None) -> int:
    if sprite is not None:
        surface.blit(sprite, (x, y - (sprite.get_height() - 18) // 2))
    draw_text(surface, name, fonts.body(14, bold=True), C.COL_TEXT, (x + 34, y + 9), align="midleft")
    draw_text(surface, value, fonts.body(14), C.COL_GOLD, (x + 170, y + 9), align="midleft")
    return y + 24


def draw_section_label(surface, x, y, text, fonts: Fonts, width: int = 0, colour=C.COL_TEXT_FAINT) -> None:
    font = fonts.body(11, bold=True)
    draw_text(surface, text.upper(), font, colour, (x, y))
    if width:
        line_y = y + 8
        start = x + font.size(text.upper())[0] + 10
        if start < x + width:
            pygame.draw.rect(surface, (40, 48, 84), (start, line_y, x + width - start, 1))


def draw_dialog_frame(surface, rect, fonts: Fonts, title: str, accent=C.COL_CYAN) -> pygame.Rect:
    """Panel with a coloured title bar. Returns the inner content rect."""
    pygame.draw.rect(surface, (4, 6, 14), rect.move(6, 6))
    pygame.draw.rect(surface, C.COL_PANEL, rect)
    pygame.draw.rect(surface, C.COL_PANEL_EDGE_LIGHT, rect, 2)
    bar = pygame.Rect(rect.x, rect.y, rect.width, 44)
    pygame.draw.rect(surface, accent, bar)
    pygame.draw.rect(surface, tuple(max(0, c - 80) for c in accent), bar, 2)
    draw_text(surface, title, fonts.heading(18), (16, 12, 24), (bar.x + 16, bar.centery - 1), align="midleft")
    return rect.inflate(-32, -60).move(0, 22)
