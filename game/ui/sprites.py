"""Procedural 16-bit style art.  Everything is generated, no image files."""

from __future__ import annotations

import math

import pygame

from engine import constants as C

TRANSPARENT = (0, 0, 0, 0)

ROBOT_PALETTE = {
    "k": (12, 15, 32, 255),
    "c": (77, 226, 240, 255),
    "d": (26, 142, 168, 255),
    "w": (223, 251, 255, 255),
    "y": (255, 230, 109, 255),
    "p": (255, 111, 181, 255),
    "g": (154, 167, 199, 255),
}

ROBOT_FRONT = [
    "................",
    ".....p....p.....",
    ".....k....k.....",
    "....kpk..kpk....",
    "..kkkkkkkkkkkk..",
    "..kcccccccccck..",
    "..kcyyccccyyck..",
    "..kcccccccccck..",
    "..kcckkkkkkcck..",
    "..kcddddddddck..",
    ".kkcccccccccckk.",
    ".kdkccccccccdk..",
    "..kkddddddddkk..",
    "...kkck..kckk...",
    "...kkk....kkk...",
    "................",
]

ROBOT_FRONT_WALK = [
    "................",
    ".....p....p.....",
    ".....k....k.....",
    "....kpk..kpk....",
    "..kkkkkkkkkkkk..",
    "..kcccccccccck..",
    "..kcyyccccyyck..",
    "..kcccccccccck..",
    "..kcckkkkkkcck..",
    "..kcddddddddck..",
    ".kkcccccccccckk.",
    ".kdkccccccccdk..",
    "..kkddddddddkk..",
    "...kck....kck...",
    "..kkk......kkk..",
    "................",
]

ROBOT_BACK = [
    "................",
    ".....p....p.....",
    ".....k....k.....",
    "....kpk..kpk....",
    "..kkkkkkkkkkkk..",
    "..kcccccccccck..",
    "..kcggggggggck..",
    "..kcgddddddgck..",
    "..kcgddddddgck..",
    "..kcddddddddck..",
    ".kkcccccccccckk.",
    ".kdkccccccccdk..",
    "..kkddddddddkk..",
    "...kkck..kckk...",
    "...kkk....kkk...",
    "................",
]

ROBOT_SIDE = [
    "................",
    "......p..p......",
    "......k..k......",
    ".....kpk.kpk....",
    "...kkkkkkkkkk...",
    "...kcccccccck...",
    "...kcccyyccck...",
    "...kcccccccck...",
    "...kcckkkkkkk...",
    "..kkcdddddddk...",
    ".kdkcccccccck...",
    "..kkcccccccck...",
    "...kddddddddk...",
    "...kkck..kck....",
    "...kkk...kkk....",
    "................",
]

CHEST_CLOSED = [
    "................",
    "................",
    "..kkkkkkkkkkkk..",
    ".kbbbbbbbbbbbbk.",
    ".kbgbbbbbbbbgbk.",
    ".kbbbbbbbbbbbbk.",
    ".kkkkkkkkkkkkkk.",
    ".kbggggggggggbk.",
    ".kbggggggggggbk.",
    ".kbbbbbbbbbbbbk.",
    ".kbbbbbbbbbbbbk.",
    ".kkkkkkkkkkkkkk.",
    "..kk........kk..",
    "................",
    "................",
    "................",
]

CHEST_OPEN = [
    "................",
    "..kkkkkkkkkkkk..",
    ".kbbbbbbbbbbbbk.",
    ".kkkkkkkkkkkkkk.",
    "..kYwYwYwYwYwYk.",
    "..kwYwYwYwYwYwk.",
    "..kkkkkkkkkkkkk.",
    ".kbggggggggggbk.",
    ".kbggggggggggbk.",
    ".kbbbbbbbbbbbbk.",
    ".kbbbbbbbbbbbbk.",
    ".kkkkkkkkkkkkkk.",
    "..kk........kk..",
    "................",
    "................",
    "................",
]

CHEST_PALETTE = {
    "k": (42, 24, 16, 255),
    "b": (160, 97, 47, 255),
    "g": (255, 205, 74, 255),
    "Y": (255, 246, 190, 255),
    "w": (255, 223, 120, 255),
}


def pixel_surface(rows: list[str], palette: dict) -> pygame.Surface:
    height = len(rows)
    width = len(rows[0])
    for row in rows:
        assert len(row) == width, f"Row length {len(row)} != {width}: {row!r}"
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            colour = palette.get(char)
            if colour:
                surface.set_at((x, y), colour)
    return surface


def scale(surface: pygame.Surface, factor: int) -> pygame.Surface:
    factor = max(1, int(factor))
    if factor == 1:
        return surface
    return pygame.transform.scale(
        surface, (surface.get_width() * factor, surface.get_height() * factor)
    )


def coin_surface(frame: int, size: int = 16) -> pygame.Surface:
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    widths = (12, 9, 5, 9)
    width = max(2, widths[frame % 4])
    rect = pygame.Rect(8 - width // 2, 3, width, 10)
    pygame.draw.ellipse(surface, (128, 84, 18, 255), rect.inflate(2, 2))
    pygame.draw.ellipse(surface, C.COL_GOLD, rect)
    inner = rect.inflate(-max(2, width // 3), -4)
    if inner.width >= 2:
        pygame.draw.ellipse(surface, (255, 236, 150), inner)
    return scale(surface, size // 16 or 1)


def base_surface() -> pygame.Surface:
    """A 24x24 stone gate with a glowing magenta portal arch."""
    surface = pygame.Surface((24, 24), pygame.SRCALPHA)
    outline = (14, 10, 30, 255)
    stone = (70, 58, 112, 255)
    stone_dark = (48, 39, 80, 255)
    void = (24, 14, 46, 255)
    # ground shadow
    pygame.draw.ellipse(surface, (10, 8, 22, 170), (1, 19, 22, 5))
    # pillars and lintel
    pygame.draw.rect(surface, outline, (2, 5, 20, 16))
    pygame.draw.rect(surface, stone, (3, 6, 18, 14))
    pygame.draw.rect(surface, stone_dark, (3, 16, 18, 4))
    # crenellations
    for x in (3, 8, 13, 18):
        pygame.draw.rect(surface, outline, (x, 1, 3, 6))
        pygame.draw.rect(surface, stone, (x + 1, 2, 1, 4))
    # arched opening
    pygame.draw.rect(surface, outline, (6, 8, 12, 13))
    pygame.draw.ellipse(surface, outline, (6, 4, 12, 9))
    pygame.draw.rect(surface, void, (7, 9, 10, 12))
    pygame.draw.ellipse(surface, void, (7, 5, 10, 9))
    # portal swirl
    pygame.draw.ellipse(surface, (104, 34, 108, 255), (9, 7, 6, 6))
    pygame.draw.ellipse(surface, (255, 111, 181, 255), (10, 8, 4, 4))
    pygame.draw.rect(surface, (255, 206, 236, 255), (11, 9, 2, 2))
    pygame.draw.rect(surface, (120, 40, 120, 255), (9, 12, 6, 2))
    pygame.draw.rect(surface, (120, 40, 120, 255), (9, 15, 6, 2))
    # runes on the pillars
    for y in (9, 13):
        pygame.draw.rect(surface, (255, 111, 181, 255), (4, y, 1, 1))
        pygame.draw.rect(surface, (255, 111, 181, 255), (19, y, 1, 1))
    return surface


def boss_surface(frame: int) -> pygame.Surface:
    surface = pygame.Surface((24, 24), pygame.SRCALPHA)
    bob = 1 if frame % 4 in (1, 2) else 0
    blink = frame % 4 == 3
    outline = (16, 8, 30, 255)
    body = (138, 77, 255, 255)
    shade = (86, 40, 160, 255)
    horn = (222, 226, 245, 255)
    eye = (255, 59, 92, 255)
    pupil = (255, 236, 120, 255)
    # horns
    pygame.draw.polygon(surface, outline, [(5, 9 + bob), (7, 1 + bob), (10, 9 + bob)])
    pygame.draw.polygon(surface, horn, [(6, 8 + bob), (7, 3 + bob), (9, 8 + bob)])
    pygame.draw.polygon(surface, outline, [(18, 9 + bob), (17, 1 + bob), (14, 9 + bob)])
    pygame.draw.polygon(surface, horn, [(17, 8 + bob), (16, 3 + bob), (15, 8 + bob)])
    # body
    pygame.draw.rect(surface, outline, (4, 7 + bob, 16, 15), border_radius=4)
    pygame.draw.rect(surface, body, (5, 8 + bob, 14, 13), border_radius=4)
    pygame.draw.rect(surface, shade, (5, 17 + bob, 14, 4), border_radius=3)
    # eyes
    if blink:
        pygame.draw.rect(surface, outline, (7, 11 + bob, 4, 1))
        pygame.draw.rect(surface, outline, (13, 11 + bob, 4, 1))
    else:
        pygame.draw.rect(surface, eye, (7, 10 + bob, 4, 4))
        pygame.draw.rect(surface, eye, (13, 10 + bob, 4, 4))
        pygame.draw.rect(surface, pupil, (8, 11 + bob, 2, 2))
        pygame.draw.rect(surface, pupil, (14, 11 + bob, 2, 2))
    # mouth
    pygame.draw.rect(surface, outline, (8, 16 + bob, 8, 3))
    for x in (8, 10, 12, 14):
        pygame.draw.rect(surface, (255, 255, 255, 255), (x, 16 + bob, 1, 1))
    # arms
    pygame.draw.rect(surface, outline, (1, 12 + bob, 3, 7))
    pygame.draw.rect(surface, body, (2, 13 + bob, 2, 5))
    pygame.draw.rect(surface, outline, (20, 12 + bob, 3, 7))
    pygame.draw.rect(surface, body, (20, 13 + bob, 2, 5))
    return surface


def _floor_surface(size: int, variant: int) -> pygame.Surface:
    surface = pygame.Surface((size, size))
    base = C.COL_FLOOR_A if variant % 2 == 0 else C.COL_FLOOR_B
    surface.fill(base)
    dark = tuple(max(0, c - 7) for c in base)
    light = tuple(min(255, c + 8) for c in base)
    step = max(4, size // 8)
    for y in range(2, size - 2, step):
        for x in range(2, size - 2, step):
            if (x * 7 + y * 13 + variant * 5) % 11 == 0:
                pygame.draw.rect(surface, dark, (x, y, 2, 2))
            elif (x * 3 + y * 5) % 17 == 0:
                pygame.draw.rect(surface, light, (x, y, 2, 2))
    pygame.draw.rect(surface, (22, 27, 48), (0, 0, size, size), 1)
    return surface


def _wall_surface(size: int, variant: int) -> pygame.Surface:
    surface = pygame.Surface((size, size))
    surface.fill(C.COL_STONE_DARK)
    brick_h = max(4, size // 4)
    brick_w = max(6, size // 2)
    for row in range(4):
        offset = (brick_w // 2) if row % 2 else 0
        for col in range(-1, 4):
            x = col * brick_w + offset
            y = row * brick_h
            rect = pygame.Rect(x + 1, y + 1, brick_w - 2, brick_h - 2)
            colour = C.COL_STONE if (row + col + variant) % 3 else (88, 95, 130)
            pygame.draw.rect(surface, colour, rect)
            pygame.draw.rect(surface, C.COL_STONE_LIGHT, (rect.x, rect.y, rect.width, 1))
            pygame.draw.rect(surface, (36, 41, 64), (rect.x, rect.bottom - 1, rect.width, 1))
    if variant % 3 == 0:
        moss = (62, 110, 92)
        pygame.draw.rect(surface, moss, (size // 4, size // 3, max(2, size // 6), max(1, size // 12)))
        pygame.draw.rect(surface, moss, (size // 4 + 2, size // 3 + 3, max(2, size // 8), max(1, size // 14)))
    return surface


def _icon_weapon(size: int) -> pygame.Surface:
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    bolt = [(9, 1), (4, 9), (8, 9), (6, 15), (12, 6), (8, 6), (11, 1)]
    pygame.draw.polygon(surface, (14, 18, 40, 255), [(x + 1, y + 1) for x, y in bolt])
    pygame.draw.polygon(surface, C.COL_GOLD, bolt)
    pygame.draw.polygon(surface, (255, 246, 190), [(9, 2), (6, 8), (9, 8), (8, 13), (11, 6), (8, 6)])
    return scale(surface, max(1, size // 16))


def _icon_route(size: int) -> pygame.Surface:
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    points = [(2, 13), (5, 13), (5, 8), (10, 8), (10, 3), (14, 3)]
    pygame.draw.lines(surface, (12, 15, 32, 255), False, [(x + 1, y + 1) for x, y in points], 3)
    pygame.draw.lines(surface, C.COL_GREEN, False, points, 2)
    pygame.draw.rect(surface, C.COL_GREEN, (12, 1, 4, 4))
    return scale(surface, max(1, size // 16))


class SpriteSet:
    """All sprites rendered for one tile size."""

    def __init__(self, tile: int) -> None:
        self.tile = tile
        self.char_scale = max(2, tile // 14)
        self.floor = [_floor_surface(tile, i) for i in range(4)]
        self.wall = [_wall_surface(tile, i) for i in range(4)]
        self.robot_front = [
            scale(pixel_surface(ROBOT_FRONT, ROBOT_PALETTE), self.char_scale),
            scale(pixel_surface(ROBOT_FRONT_WALK, ROBOT_PALETTE), self.char_scale),
        ]
        self.robot_back = [
            scale(pixel_surface(ROBOT_BACK, ROBOT_PALETTE), self.char_scale),
            scale(pixel_surface(ROBOT_BACK, ROBOT_PALETTE), self.char_scale),
        ]
        side = pixel_surface(ROBOT_SIDE, ROBOT_PALETTE)
        self.robot_right = [scale(side, self.char_scale), scale(side, self.char_scale)]
        flipped = pygame.transform.flip(side, True, False)
        self.robot_left = [scale(flipped, self.char_scale), scale(flipped, self.char_scale)]
        self.coin = [scale(coin_surface(i, 16).convert_alpha(), self.char_scale) for i in range(4)]
        self.chest_closed = scale(pixel_surface(CHEST_CLOSED, CHEST_PALETTE), self.char_scale)
        self.chest_open = scale(pixel_surface(CHEST_OPEN, CHEST_PALETTE), self.char_scale)
        self.base = scale(base_surface(), max(2, round(tile / 16)))
        boss_scale = max(1, int(tile / 10))
        self.boss = [scale(boss_surface(i), boss_scale) for i in range(4)]
        self.icon_weapon = _icon_weapon(tile)
        self.icon_route = _icon_route(tile)

    def robot(self, facing: int, frame: int = 0) -> pygame.Surface:
        table = {
            0: self.robot_back,
            1: self.robot_right,
            2: self.robot_front,
            3: self.robot_left,
        }
        return table[facing][frame % len(table[facing])]


class SpriteBank:
    def __init__(self) -> None:
        self._sets: dict[int, SpriteSet] = {}

    def at(self, tile: int) -> SpriteSet:
        if tile not in self._sets:
            self._sets[tile] = SpriteSet(tile)
        return self._sets[tile]
