"""Generate the window icon and a sprite preview sheet.

Run from the game/ folder:
    python tools/build_assets.py
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import constants as C  # noqa: E402
from ui.theme import Fonts, draw_text  # noqa: E402
from ui.sprites import SpriteBank  # noqa: E402

ASSETS = os.path.join(ROOT, "assets")


def build_icon() -> None:
    bank = SpriteBank()
    sprites = bank.at(16)
    robot = sprites.robot_front[0]
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    icon.blit(robot, robot.get_rect(center=(16, 17)))
    pygame.image.save(icon, os.path.join(ASSETS, "icon.png"))


def build_preview() -> None:
    fonts = Fonts()
    bank = SpriteBank()
    tile = 48
    sprites = bank.at(tile)
    entries: list[tuple[str, pygame.Surface]] = [
        ("Robot up", sprites.robot(facing=0, frame=0)),
        ("Robot right", sprites.robot(facing=1, frame=0)),
        ("Robot down", sprites.robot(facing=2, frame=0)),
        ("Robot left", sprites.robot(facing=3, frame=0)),
        ("Coin 1", sprites.coin[0]),
        ("Coin 2", sprites.coin[1]),
        ("Coin 3", sprites.coin[2]),
        ("Coin 4", sprites.coin[3]),
        ("Chest", sprites.chest_closed),
        ("Chest open", sprites.chest_open),
        ("Enemy base", sprites.base),
        ("Boss 1", sprites.boss[0]),
        ("Boss 2", sprites.boss[1]),
        ("Floor A", sprites.floor[0]),
        ("Floor B", sprites.floor[1]),
        ("Wall A", sprites.wall[0]),
        ("Wall B", sprites.wall[1]),
    ]
    columns = 6
    cell_w, cell_h = 150, 130
    rows = (len(entries) + columns - 1) // columns
    sheet = pygame.Surface((columns * cell_w, rows * cell_h + 56))
    sheet.fill(C.COL_BG)
    draw_text(sheet, "PYTHON MAZE ADVENTURE  -  16-BIT SPRITE SHEET", fonts.heading(20),
              C.COL_GOLD, (20, 14))
    for index, (label, image) in enumerate(entries):
        col, row = index % columns, index // columns
        cx = col * cell_w + cell_w // 2
        cy = 56 + row * cell_h + 62
        pygame.draw.rect(sheet, C.COL_PANEL, (col * cell_w + 8, 56 + row * cell_h + 8,
                                              cell_w - 16, cell_h - 16))
        pygame.draw.rect(sheet, C.COL_PANEL_EDGE, (col * cell_w + 8, 56 + row * cell_h + 8,
                                                   cell_w - 16, cell_h - 16), 1)
        sheet.blit(image, image.get_rect(center=(cx, cy)))
        draw_text(sheet, label, fonts.body(12, bold=True), C.COL_TEXT_DIM,
                  (cx, 56 + row * cell_h + cell_h - 26), align="center")
    pygame.image.save(sheet, os.path.join(ASSETS, "sprites_preview.png"))


def main() -> None:
    pygame.init()
    pygame.display.set_mode((10, 10))
    os.makedirs(ASSETS, exist_ok=True)
    build_icon()
    build_preview()
    print("Wrote", os.path.join(ASSETS, "icon.png"))
    print("Wrote", os.path.join(ASSETS, "sprites_preview.png"))


if __name__ == "__main__":
    main()
