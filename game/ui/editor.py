"""A small code editor: a pure-Python ``Document`` plus a pygame view.

``Document`` holds only text and cursor state, so it can be unit-tested
without a display.  ``Editor`` adds drawing, scrolling, syntax colouring
and event handling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pygame

from engine import constants as C
from ui.theme import Fonts, draw_text

KEYWORDS = {
    "if", "elif", "else", "for", "in", "def", "return", "and", "or", "not",
    "True", "False", "None", "while", "break", "continue", "pass", "import", "from",
}
GAME_API = {
    "move_one_step_up", "move_one_step_down", "move_one_step_left",
    "move_one_step_right", "fire_super_attack",
    "coins", "player_name", "weapon_power",
}
BUILTINS = {"int", "str", "float", "bool", "print", "input", "range", "len", "abs", "round", "min", "max"}

TOKEN_COLOURS = {
    "keyword": (198, 154, 255),
    "api": C.COL_CYAN,
    "builtin": C.COL_GREEN,
    "name": C.COL_TEXT,
    "number": C.COL_GOLD,
    "string": C.COL_ORANGE,
    "comment": (116, 138, 128),
}

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
INDENT = "    "


def tokenise(line: str) -> list[tuple[int, int, str]]:
    """Split one source line into (start, end, kind) spans."""
    tokens: list[tuple[int, int, str]] = []
    i = 0
    length = len(line)
    previous_word = ""
    while i < length:
        char = line[i]
        if char == "#":
            tokens.append((i, length, "comment"))
            break
        if char in "\"'":
            j = i + 1
            while j < length:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == char:
                    j += 1
                    break
                j += 1
            tokens.append((i, min(j, length), "string"))
            i = j
            continue
        if char.isdigit():
            j = i
            while j < length and (line[j].isdigit() or line[j] == "."):
                j += 1
            tokens.append((i, j, "number"))
            i = j
            continue
        match = WORD_RE.match(line, i)
        if match:
            word = match.group(0)
            if word in KEYWORDS:
                kind = "keyword"
            elif word in GAME_API:
                kind = "api"
            elif word in BUILTINS:
                kind = "builtin"
            elif previous_word == "def":
                kind = "api"
            else:
                kind = "name"
            tokens.append((i, match.end(), kind))
            previous_word = word
            i = match.end()
            continue
        if not char.isspace():
            previous_word = ""
        i += 1
    return tokens


@dataclass
class Document:
    lines: list[str] = field(default_factory=lambda: [""])
    row: int = 0
    col: int = 0
    desired_col: int | None = None
    anchor: tuple[int, int] | None = None
    error_line: int | None = None
    _undo: list[tuple[list[str], int, int]] = field(default_factory=list)
    _redo: list[tuple[list[str], int, int]] = field(default_factory=list)

    # -------------------------------------------------------------- basics
    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def line(self, index: int | None = None) -> str:
        index = self.row if index is None else index
        index = max(0, min(len(self.lines) - 1, index))
        return self.lines[index]

    def clamp(self) -> None:
        self.row = max(0, min(len(self.lines) - 1, self.row))
        self.col = max(0, min(len(self.lines[self.row]), self.col))

    def set_text(self, text: str) -> None:
        clean = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", INDENT)
        self.lines = clean.split("\n") or [""]
        self.row = len(self.lines) - 1
        self.col = len(self.lines[-1])
        self.anchor = None
        self.desired_col = None
        self._undo.clear()
        self._redo.clear()
        self.error_line = None

    # ------------------------------------------------------------ selection
    def selection(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        if self.anchor is None:
            return None
        start, end = (self.anchor, (self.row, self.col))
        if (start[0], start[1]) > (end[0], end[1]):
            start, end = end, start
        if start == end:
            return None
        return start, end

    def selected_text(self) -> str:
        span = self.selection()
        if span is None:
            return ""
        (r1, c1), (r2, c2) = span
        if r1 == r2:
            return self.lines[r1][c1:c2]
        parts = [self.lines[r1][c1:]]
        parts.extend(self.lines[r1 + 1:r2])
        parts.append(self.lines[r2][:c2])
        return "\n".join(parts)

    def select_all(self) -> None:
        self.anchor = (0, 0)
        self.row = len(self.lines) - 1
        self.col = len(self.lines[-1])

    def clear_selection(self) -> None:
        self.anchor = None

    # --------------------------------------------------------------- history
    def _snapshot(self) -> tuple[list[str], int, int]:
        return (list(self.lines), self.row, self.col)

    def push_undo(self) -> None:
        self._undo.append(self._snapshot())
        if len(self._undo) > 200:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append(self._snapshot())
        self.lines, self.row, self.col = self._undo.pop()
        self.anchor = None
        self.clamp()

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append(self._snapshot())
        self.lines, self.row, self.col = self._redo.pop()
        self.anchor = None
        self.clamp()

    # ---------------------------------------------------------------- edits
    def delete_selection(self) -> bool:
        span = self.selection()
        if span is None:
            return False
        (r1, c1), (r2, c2) = span
        merged = self.lines[r1][:c1] + self.lines[r2][c2:]
        self.lines[r1:r2 + 1] = [merged]
        self.row, self.col = r1, c1
        self.anchor = None
        self.desired_col = None
        return True

    def insert(self, text: str, record: bool = True) -> None:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text:
            return
        if record:
            self.push_undo()
        self.delete_selection()
        pieces = text.split("\n")
        head = self.lines[self.row][:self.col]
        tail = self.lines[self.row][self.col:]
        if len(pieces) == 1:
            self.lines[self.row] = head + pieces[0] + tail
            self.col += len(pieces[0])
        else:
            new_lines = [head + pieces[0]] + pieces[1:-1] + [pieces[-1] + tail]
            self.lines[self.row:self.row + 1] = new_lines
            self.row += len(pieces) - 1
            self.col = len(pieces[-1])
        self.desired_col = None
        self.error_line = None

    def insert_spaces(self, count: int = 4, record: bool = True) -> None:
        self.insert(" " * count, record=record)

    def newline(self) -> None:
        if self.selection() is not None:
            self.delete_selection()
        self.push_undo()
        current = self.lines[self.row]
        head = current[:self.col]
        tail = current[self.col:]
        leading = len(head) - len(head.lstrip(" "))
        indent = " " * leading
        if head.rstrip().endswith(":"):
            indent += INDENT
        self.lines[self.row] = head
        self.lines.insert(self.row + 1, indent + tail)
        self.row += 1
        self.col = len(indent)
        self.desired_col = None
        self.error_line = None

    def backspace(self) -> None:
        if self.selection() is not None:
            self.push_undo()
            self.delete_selection()
            return
        if self.col > 0:
            self.push_undo()
            line = self.lines[self.row]
            if line[self.col - 4:self.col] == INDENT and self.col >= 4 and line[:self.col].strip() == "":
                self.lines[self.row] = line[:self.col - 4] + line[self.col:]
                self.col -= 4
            else:
                self.lines[self.row] = line[:self.col - 1] + line[self.col:]
                self.col -= 1
            self.error_line = None
        elif self.row > 0:
            self.push_undo()
            previous = self.lines[self.row - 1]
            self.col = len(previous)
            self.lines[self.row - 1] = previous + self.lines[self.row]
            del self.lines[self.row]
            self.row -= 1
            self.error_line = None

    def delete(self) -> None:
        if self.selection() is not None:
            self.push_undo()
            self.delete_selection()
            return
        line = self.lines[self.row]
        if self.col < len(line):
            self.push_undo()
            self.lines[self.row] = line[:self.col] + line[self.col + 1:]
            self.error_line = None
        elif self.row < len(self.lines) - 1:
            self.push_undo()
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]
            self.error_line = None

    def indent_block(self, dedent: bool = False) -> None:
        span = self.selection()
        if span is not None:
            start_row, end_row = span[0][0], span[1][0]
        else:
            start_row = end_row = self.row
        self.push_undo()
        for index in range(start_row, end_row + 1):
            line = self.lines[index]
            if dedent:
                if line.startswith(INDENT):
                    self.lines[index] = line[4:]
                elif line.startswith(" "):
                    self.lines[index] = line[1:]
            else:
                self.lines[index] = INDENT + line
        if span is not None:
            self.anchor = (start_row, span[0][1] + (0 if dedent else 4))
            self.row, self.col = end_row, min(len(self.lines[end_row]), span[1][1] + (0 if dedent else 4))
        else:
            self.col = min(len(self.lines[self.row]), self.col + (-4 if dedent else 4))
        self.desired_col = None

    # -------------------------------------------------------------- motion
    def _vertical(self, delta: int) -> None:
        if self.desired_col is None:
            self.desired_col = self.col
        self.row = max(0, min(len(self.lines) - 1, self.row + delta))
        self.col = min(len(self.lines[self.row]), self.desired_col)
        self.anchor = None

    def move(self, delta_row: int = 0, delta_col: int = 0, extend: bool = False) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.col)
        if delta_row:
            self._vertical(delta_row)
            return
        if not extend:
            self.anchor = None
        self.desired_col = None
        target = (self.row, self.col + delta_col)
        if delta_col < 0 and self.col == 0 and self.row > 0:
            self.row -= 1
            self.col = len(self.lines[self.row])
            return
        if delta_col > 0 and self.col >= len(self.lines[self.row]) and self.row < len(self.lines) - 1:
            self.row += 1
            self.col = 0
            return
        self.col = max(0, min(len(self.lines[self.row]), target[1]))

    def home(self, extend: bool = False) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.col)
        elif not extend:
            self.anchor = None
        line = self.lines[self.row]
        stripped = len(line) - len(line.lstrip(" "))
        self.col = 0 if self.col == stripped else stripped
        self.desired_col = None

    def end(self, extend: bool = False) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.col)
        elif not extend:
            self.anchor = None
        self.col = len(self.lines[self.row])
        self.desired_col = None

    def set_cursor(self, row: int, col: int, extend: bool = False) -> None:
        if extend and self.anchor is None:
            self.anchor = (self.row, self.col)
        elif not extend:
            self.anchor = None
        self.row = max(0, min(len(self.lines) - 1, row))
        self.col = max(0, min(len(self.lines[self.row]), col))
        self.desired_col = None


class Editor:
    """Interactive view over a Document."""

    def __init__(self, document: Document, font: pygame.font.Font) -> None:
        self.doc = document
        self.font = font
        self.placeholder = ""
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.scroll_row = 0
        self.scroll_x = 0
        self.focused = False
        self.caret_dirty_at = 0.0
        self.line_height = font.get_linesize() + 3
        self.gutter = 44
        self.pad = 8
        self._token_cache: dict[str, list[tuple[int, int, str]]] = {}
        self._dragging = False
        self.mouse_pos = (0, 0)
        self.clipboard = ""
        self._char_width = font.size("M")[0]

    # --------------------------------------------------------------- layout
    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect

    @property
    def text_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x + self.gutter + self.pad,
            self.rect.y + self.pad,
            self.rect.width - self.gutter - self.pad * 2 - 10,
            self.rect.height - self.pad * 2,
        )

    def visible_rows(self) -> int:
        return max(1, self.text_rect.height // self.line_height)

    def tokens(self, line: str) -> list[tuple[int, int, str]]:
        cached = self._token_cache.get(line)
        if cached is None:
            cached = tokenise(line)
            if len(self._token_cache) > 3000:
                self._token_cache.clear()
            self._token_cache[line] = cached
        return cached

    def ensure_visible(self) -> None:
        rows = self.visible_rows()
        if self.doc.row < self.scroll_row:
            self.scroll_row = self.doc.row
        elif self.doc.row >= self.scroll_row + rows:
            self.scroll_row = self.doc.row - rows + 1
        caret_x = self.font.size(self.doc.line()[:self.doc.col])[0]
        width = self.text_rect.width
        if caret_x - self.scroll_x > width - 20:
            self.scroll_x = caret_x - width + 20
        if caret_x < self.scroll_x:
            self.scroll_x = max(0, caret_x - 20)

    # --------------------------------------------------------------- events
    def pos_to_cursor(self, pos) -> tuple[int, int]:
        text_rect = self.text_rect
        row = self.scroll_row + max(0, (pos[1] - text_rect.y) // self.line_height)
        row = max(0, min(len(self.doc.lines) - 1, row))
        x = pos[0] - text_rect.x + self.scroll_x
        line = self.doc.lines[row]
        col = 0
        best = abs(x)
        for index in range(1, len(line) + 1):
            distance = abs(self.font.size(line[:index])[0] - x)
            if distance < best:
                best = distance
                col = index
        return row, col

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True when the event was used by the editor."""
        doc = self.doc
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.focused = True
                row, col = self.pos_to_cursor(event.pos)
                doc.set_cursor(row, col)
                self._dragging = True
                self.caret_dirty_at = 0.0
                return True
            self.focused = False
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self._dragging
            self._dragging = False
            return was_dragging and self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEMOTION and self._dragging:
            if self.rect.collidepoint(event.pos):
                row, col = self.pos_to_cursor(event.pos)
                doc.set_cursor(row, col, extend=True)
            return True
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(self.mouse_pos):
                self.scroll_row = max(0, self.scroll_row - event.y * 3)
                return True
            return False
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            if event.text:
                doc.insert(event.text)
                self.ensure_visible()
                self.caret_dirty_at = 0.0
            return True
        if event.type != pygame.KEYDOWN:
            return False
        ctrl = event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)
        shift = event.mod & pygame.KMOD_SHIFT
        key = event.key
        if ctrl and key == pygame.K_a:
            doc.select_all()
            return True
        if ctrl and key == pygame.K_c:
            chosen = doc.selected_text()
            if chosen:
                self.clipboard = chosen
            return True
        if ctrl and key == pygame.K_x:
            self.clipboard = doc.selected_text()
            doc.push_undo()
            doc.delete_selection()
            return True
        if ctrl and key == pygame.K_v:
            doc.insert(self.clipboard)
            self.ensure_visible()
            return True
        if ctrl and key == pygame.K_z:
            doc.undo()
            self.ensure_visible()
            return True
        if ctrl and (key == pygame.K_y or (key == pygame.K_z and shift)):
            doc.redo()
            self.ensure_visible()
            return True
        if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            if key == pygame.K_LEFT:
                doc.move(delta_col=-1, extend=bool(shift))
            elif key == pygame.K_RIGHT:
                doc.move(delta_col=1, extend=bool(shift))
            elif key == pygame.K_UP:
                doc.move(delta_row=-1, extend=bool(shift))
            else:
                doc.move(delta_row=1, extend=bool(shift))
            self.ensure_visible()
            self.caret_dirty_at = 0.0
            return True
        if key == pygame.K_HOME:
            doc.home(extend=bool(shift))
            self.scroll_x = 0
            self.ensure_visible()
            return True
        if key == pygame.K_END:
            doc.end(extend=bool(shift))
            self.ensure_visible()
            return True
        if key == pygame.K_PAGEUP:
            doc.move(delta_row=-self.visible_rows())
            self.ensure_visible()
            return True
        if key == pygame.K_PAGEDOWN:
            doc.move(delta_row=self.visible_rows())
            self.ensure_visible()
            return True
        if key == pygame.K_RETURN:
            doc.newline()
            self.ensure_visible()
            return True
        if key == pygame.K_BACKSPACE:
            doc.backspace()
            self.ensure_visible()
            return True
        if key == pygame.K_DELETE:
            doc.delete()
            self.ensure_visible()
            return True
        if key == pygame.K_TAB:
            if doc.selection() is not None and doc.selection()[0][0] != doc.selection()[1][0]:
                doc.indent_block(dedent=bool(shift))
            elif shift:
                doc.indent_block(dedent=True)
            else:
                doc.insert_spaces(4)
            self.ensure_visible()
            return True
        if key == pygame.K_ESCAPE:
            self.focused = False
            return True
        return False

    # ----------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, now: float) -> None:
        rect = self.rect
        pygame.draw.rect(surface, C.COL_BG_DEEP, rect)
        pygame.draw.rect(surface, C.COL_PANEL_EDGE if self.focused else (40, 48, 84), rect, 2)
        gutter_rect = pygame.Rect(rect.x + 2, rect.y + 2, self.gutter, rect.height - 4)
        pygame.draw.rect(surface, (14, 18, 36), gutter_rect)
        pygame.draw.line(
            surface, (40, 48, 84), (gutter_rect.right, rect.y + 2), (gutter_rect.right, rect.bottom - 3)
        )
        text_rect = self.text_rect
        clip_old = surface.get_clip()
        surface.set_clip(text_rect)
        doc = self.doc
        rows = self.visible_rows()
        self.ensure_visible()
        selection = doc.selection()
        base_x = text_rect.x - self.scroll_x
        for offset in range(rows):
            index = self.scroll_row + offset
            if index >= len(doc.lines):
                break
            y = text_rect.y + offset * self.line_height
            line_rect = pygame.Rect(text_rect.x, y - 1, text_rect.width, self.line_height)
            if index == doc.row and self.focused:
                pygame.draw.rect(surface, (22, 28, 54), line_rect)
            if doc.error_line == index + 1:
                pygame.draw.rect(surface, (60, 22, 32), line_rect)
            line = doc.lines[index]
            if selection is not None:
                (r1, c1), (r2, c2) = selection
                if r1 <= index <= r2:
                    start_col = c1 if index == r1 else 0
                    end_col = c2 if index == r2 else len(line)
                    x1 = base_x + self.font.size(line[:start_col])[0]
                    x2 = base_x + self.font.size(line[:end_col])[0]
                    if end_col > start_col:
                        pygame.draw.rect(surface, (44, 62, 118), (x1, y - 1, max(2, x2 - x1), self.line_height))
            x = base_x
            painted = 0
            for start, end, kind in self.tokens(line):
                if start < painted:
                    continue
                if start > painted:
                    gap = line[painted:start]
                    if gap.strip():
                        surface.blit(self.font.render(gap, True, C.COL_TEXT), (x, y))
                    x += self.font.size(gap)[0]
                piece = line[start:end]
                image = self.font.render(piece, True, TOKEN_COLOURS.get(kind, C.COL_TEXT))
                surface.blit(image, (x, y))
                x += self.font.size(piece)[0]
                painted = end
            if painted < len(line):
                tail = line[painted:]
                if tail.strip():
                    surface.blit(self.font.render(tail, True, C.COL_TEXT), (x, y))
        surface.set_clip(clip_old)
        # faint guidance while the editor is empty
        if not doc.text.strip() and self.placeholder:
            for offset, hint in enumerate(self.placeholder.split("\n")[:rows]):
                draw_text(
                    surface,
                    hint,
                    self.font,
                    C.COL_TEXT_FAINT,
                    (text_rect.x, text_rect.y + offset * self.line_height),
                    align="topleft",
                )
        # gutter numbers
        for offset in range(rows):
            index = self.scroll_row + offset
            if index >= len(doc.lines):
                break
            y = text_rect.y + offset * self.line_height
            colour = C.COL_GOLD if index == doc.row else (74, 86, 130)
            draw_text(surface, str(index + 1), self.font, colour,
                      (gutter_rect.right - 8, y), align="topright")
        # caret
        if self.focused:
            blink_on = ((now - self.caret_dirty_at) % 1.0) < 0.55 or self.caret_dirty_at == 0.0
            if blink_on:
                line = doc.line()
                cx = base_x + self.font.size(line[:doc.col])[0]
                cy = text_rect.y + (doc.row - self.scroll_row) * self.line_height
                if text_rect.collidepoint(cx, cy):
                    pygame.draw.rect(surface, C.COL_CYAN, (cx, cy, 2, self.line_height - 2))
        # scrollbar
        if len(doc.lines) > rows:
            track = pygame.Rect(rect.right - 8, text_rect.y, 4, text_rect.height)
            pygame.draw.rect(surface, (18, 22, 42), track)
            height = max(18, int(track.height * rows / len(doc.lines)))
            pos = int((track.height - height) * (self.scroll_row / max(1, len(doc.lines) - rows)))
            pygame.draw.rect(surface, (70, 84, 132), (track.x, track.y + pos, track.width, height))
