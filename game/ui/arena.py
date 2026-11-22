"""The animated maze panel: tiles, robot, supplies, boss and effects."""

from __future__ import annotations

import math

import pygame

from engine import constants as C
from ui.sprites import SpriteBank
from ui.theme import Fonts, draw_text


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class ArenaView:
    def __init__(self, session, bank: SpriteBank, fonts: Fonts) -> None:
        self.session = session
        self.bank = bank
        self.fonts = fonts
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.hover: tuple[int, int] | None = None
        self._path: list[tuple[int, int]] | None = None
        self.tile = 32
        self.origin = (0, 0)

    def invalidate(self) -> None:
        self._path = None

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect
        maze = self.session.maze
        self.tile = max(12, min(rect.width // maze.width, rect.height // maze.height))
        width = self.tile * maze.width
        height = self.tile * maze.height
        self.origin = (rect.x + (rect.width - width) // 2, rect.y + (rect.height - height) // 2)
        self.maze_size = (width, height)

    def cell_rect(self, x: int, y: int) -> pygame.Rect:
        return pygame.Rect(
            self.origin[0] + x * self.tile, self.origin[1] + y * self.tile, self.tile, self.tile
        )

    def cell_center(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(self.origin[0] + (x + 0.5) * self.tile),
            int(self.origin[1] + (y + 0.5) * self.tile),
        )

    def cell_at(self, pos) -> tuple[int, int] | None:
        maze = self.session.maze
        x = (pos[0] - self.origin[0]) // self.tile
        y = (pos[1] - self.origin[1]) // self.tile
        if 0 <= x < maze.width and 0 <= y < maze.height:
            return int(x), int(y)
        return None

    def route(self) -> list[tuple[int, int]]:
        if self._path is None:
            path = None
            get_reference = getattr(self.session, "current_reference_path", None)
            if get_reference is not None:
                path = get_reference()
            self._path = path or self.session.maze.shortest_path()
        return self._path

    def hovered_cell(self, pos) -> tuple[int, int] | None:
        if not self.rect.collidepoint(pos):
            return None
        cell = self.cell_at(pos)
        if cell and not self.session.maze.is_wall(*cell):
            return cell
        return None

    # ----------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, now: float, show_route: bool) -> None:
        session = self.session
        maze = session.maze
        sprites = self.bank.at(self.tile)
        mx, my = self.origin
        width, height = self.maze_size
        surface.fill((10, 12, 26), self.rect)
        for y in range(maze.height):
            for x in range(maze.width):
                cell = self.cell_rect(x, y)
                if maze.is_wall(x, y):
                    surface.blit(sprites.wall[(x * 3 + y * 5) % 4], cell.topleft)
                else:
                    surface.blit(sprites.floor[(x * 5 + y * 3) % 4], cell.topleft)

        def blob_center(x, y):
            centre = self.cell_center(x, y)
            return (centre[0] - mx, centre[1] - my)

        # hints and glows live underneath the characters
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        if show_route and self.route():
            pulse = 0.55 + 0.45 * math.sin(now * 4)
            radius = max(3, self.tile // 9)
            for index, (x, y) in enumerate(self.route()):
                cx, cy = blob_center(x, y)
                pygame.draw.circle(overlay, (255, 205, 74, int(70 * pulse)), (cx, cy), radius + 2)
                pygame.draw.circle(overlay, (255, 224, 120, int(215 * pulse)), (cx, cy), radius)
                if index % 2 == 0:
                    pygame.draw.circle(overlay, (255, 250, 210, int(230 * pulse)), (cx, cy), max(1, radius - 2))
        base_x, base_y = maze.base
        glow = 0.5 + 0.5 * math.sin(now * 2.2)
        pygame.draw.circle(overlay, (255, 111, 181, int(30 + 46 * glow)),
                           blob_center(base_x, base_y), int(self.tile * 0.62))
        if maze.goal is not None:
            gx, gy = blob_center(*maze.goal)
            pulse = 0.5 + 0.5 * math.sin(now * 3.4)
            pygame.draw.circle(overlay, (20, 80, 100, 70), (gx, gy), int(self.tile * 0.48))
            pygame.draw.circle(overlay, (77, 226, 240, int(90 + 80 * pulse)),
                               (gx, gy), int(self.tile * 0.44), max(2, self.tile // 14))
            pygame.draw.circle(overlay, (160, 250, 255, int(60 + 70 * pulse)),
                               (gx, gy), int(self.tile * (0.28 + 0.06 * pulse)), max(1, self.tile // 22))
        if self.hover:
            cell = self.cell_rect(*self.hover).move(-mx, -my)
            pygame.draw.rect(overlay, (77, 226, 240, 60), cell, 2)
        surface.blit(overlay, (mx, my))

        # supplies
        for (x, y), supply in session.supplies_left.items():
            centre = self.cell_center(x, y)
            if supply.kind == "coin":
                image = sprites.coin[int(now * 7) % 4]
                bob = math.sin(now * 3 + x) * 2
            else:
                image = sprites.chest_closed
                bob = 0
            surface.blit(image, image.get_rect(center=(centre[0], centre[1] - 2 + bob)))

        # base portal
        base_centre = self.cell_center(base_x, base_y)
        base_image = sprites.base
        if session.stage == C.STAGE_BOSS and not session.boss_defeated:
            base_image = base_image.copy()
            base_image.set_alpha(110)
        surface.blit(base_image, base_image.get_rect(center=base_centre))

        # attack pad label sits above the goal tile
        if maze.goal is not None:
            pad = self.cell_center(*maze.goal)
            draw_text(surface, "ATTACK", self.fonts.body(9, bold=True), C.COL_CYAN,
                      (pad[0], pad[1] - self.tile // 2 - 1), align="midbottom", shadow=(0, 0, 0))

        # boss
        if session.stage == C.STAGE_BOSS and not session.boss_defeated:
            image = sprites.boss[int(now * 3.2) % 4]
            bob = math.sin(now * 2.4) * self.tile * 0.06
            centre = (base_centre[0], base_centre[1] - self.tile * 0.15 + bob)
            shadow = pygame.Rect(0, 0, int(image.get_width() * 0.6), max(5, int(image.get_height() * 0.12)))
            shadow.center = (base_centre[0], base_centre[1] + self.tile // 2 - 4)
            pygame.draw.ellipse(surface, (8, 6, 18), shadow)
            surface.blit(image, image.get_rect(center=centre))

        # robot
        px, py = float(session.player.x), float(session.player.y)
        facing = session.player.facing
        walking = False
        if session.anim is not None:
            anim = session.anim
            t = _ease(anim.progress(now))
            if anim.turn_only:
                facing = anim.facing_to if t > 0.4 else anim.facing_from
            else:
                px = _lerp(anim.from_x, anim.to_x, t)
                py = _lerp(anim.from_y, anim.to_y, t)
                facing = anim.facing_to if t > 0.66 else anim.facing_from
                walking = t < 1.0
        step_frame = 1 if walking and int(now * 14) % 2 else 0
        robot = sprites.robot(facing, step_frame)
        centre = self.cell_center(px, py)
        bob = -2 if step_frame else 0
        shadow = pygame.Rect(0, 0, int(self.tile * 0.55), max(4, int(self.tile * 0.18)))
        shadow.center = (centre[0], centre[1] + int(self.tile * 0.34))
        pygame.draw.ellipse(surface, (8, 10, 22), shadow)
        surface.blit(robot, robot.get_rect(center=(centre[0], centre[1] + bob)))
        if session.stage == C.STAGE_CREATE and py > 1:
            label = session.player_name if session.has_character else "Explorer"
            draw_text(surface, label.upper(), self.fonts.body(10, bold=True), C.COL_TEXT_DIM,
                      (centre[0], centre[1] - self.tile // 2 - 2), align="midbottom", shadow=(0, 0, 0))

        # effects animate above everything
        if session.effects:
            fx = pygame.Surface((width, height), pygame.SRCALPHA)
            for effect in session.effects:
                self._draw_effect(fx, effect, now, blob_center)
            surface.blit(fx, (mx, my))

    def _draw_effect(self, overlay, effect, now, blob_center) -> None:
        p = effect.progress(now)
        cx, cy = blob_center(effect.x, effect.y)
        tile = self.tile
        if effect.kind == "pickup":
            rise = 26 * p
            alpha = int(255 * (1 - p) ** 0.7)
            colour = (*effect.colour, alpha)
            font = self.fonts.heading(16)
            image = font.render(effect.text, True, effect.colour[:3])
            image.set_alpha(alpha)
            overlay.blit(image, image.get_rect(center=(cx, cy - tile * 0.4 - rise)))
            for index in range(6):
                angle = index * (math.tau / 6) + p * 2
                distance = 8 + 24 * p
                px = cx + math.cos(angle) * distance
                py = cy + math.sin(angle) * distance - rise * 0.4
                pygame.draw.rect(overlay, colour, (px - 2, py - 2, 3, 3))
        elif effect.kind == "bump":
            alpha = int(220 * (1 - p))
            if effect.text:
                font = self.fonts.heading(13)
                image = font.render(effect.text, True, effect.colour)
                image.set_alpha(alpha)
                overlay.blit(image, image.get_rect(center=(cx, cy - tile * 0.55 - 10 * p)))
            for index in range(4):
                angle = index * math.pi / 2 + math.pi / 4
                distance = tile * 0.2 + 10 * p
                px = cx + math.cos(angle) * distance
                py = cy + math.sin(angle) * distance
                pygame.draw.rect(overlay, (*effect.colour, alpha), (px - 2, py - 2, 4, 4))
        elif effect.kind == "beam":
            start = self.cell_center(self.session.player.x, self.session.player.y)
            end = blob_center(*self.session.maze.base)
            sx, sy = start[0] - self.origin[0], start[1] - self.origin[1]
            width = max(2.0, 7.0 * math.sin(min(1.0, p * 3.2) * math.pi / 2))
            if p < 0.85:
                for spread, colour, alpha in ((width * 2.2, (40, 170, 200), 90),
                                              (width, (77, 226, 240), 230),
                                              (max(1, width * 0.4), (240, 255, 255), 255)):
                    pygame.draw.line(overlay, (*colour, int(alpha * (1 - p))), (sx, sy), end, int(spread))
                steps = 10
                for index in range(steps):
                    t = ((now * 2.4) + index / steps) % 1.0
                    bx = _lerp(sx, end[0], t)
                    by = _lerp(sy, end[1], t) + math.sin(t * 12 + now * 8) * 4
                    pygame.draw.circle(overlay, (255, 255, 255, int(180 * (1 - p))),
                                       (int(bx), int(by)), max(1, int(width * 0.35)))
            else:
                pygame.draw.circle(overlay, (255, 255, 255, int(255 * (1 - p))), end, int(18 * (1 - p) + 4))
        elif effect.kind == "explode":
            for index, colour in enumerate(((255, 226, 120), (255, 150, 90), (255, 92, 92))):
                radius = int((tile * 0.2 + tile * 1.15 * p) * (1 - index * 0.22))
                pygame.draw.circle(overlay, (*colour, int(160 * (1 - p))), (cx, cy), max(2, radius), 3)
            for index in range(10):
                angle = index * (math.tau / 10) + 0.3
                distance = tile * 0.3 + tile * 1.4 * p
                px = cx + math.cos(angle) * distance
                py = cy + math.sin(angle) * distance
                pygame.draw.rect(overlay, (255, 205, 74, int(220 * (1 - p))), (px - 2, py - 2, 4, 4))
        elif effect.kind == "fizzle":
            for index in range(8):
                angle = index * (math.tau / 8)
                distance = tile * (0.15 + 0.5 * p)
                px = cx + math.cos(angle) * distance
                py = cy + math.sin(angle) * distance + tile * 0.3 * p * p
                pygame.draw.rect(overlay, (*effect.colour, int(200 * (1 - p))), (px - 2, py - 2, 3, 3))
        elif effect.kind == "confetti":
            colours = (C.COL_CYAN, C.COL_MAGENTA, C.COL_GOLD, C.COL_GREEN)
            for index in range(18):
                start_angle = index * (math.tau / 18)
                distance = tile * (0.3 + 0.9 * p)
                px = cx + math.cos(start_angle) * distance
                py = cy + math.sin(start_angle) * distance * 0.6 + tile * 1.4 * p * p
                colour = colours[index % 4]
                pygame.draw.rect(overlay, (*colour, int(230 * (1 - p))), (px - 2, py - 2, 4, 4))
