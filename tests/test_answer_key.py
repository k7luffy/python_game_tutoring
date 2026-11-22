"""The teacher answer key must exist, stay offline and match the game data."""

from __future__ import annotations

import html
import re

from conftest import ROOT

from engine import constants as C
from missions import mission_one

KEY = ROOT / "answers" / "answer_key.html"
LEVELS = mission_one.LEVELS


def norm(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def source() -> str:
    return KEY.read_text(encoding="utf-8")


def sections() -> dict[str, str]:
    text = source()
    found: dict[str, str] = {}
    for match in re.finditer(r'<section\b[^>]*data-(route|answer)="([^"]+)"[^>]*>', text, re.I):
        end = text.find("</section>", match.end())
        assert end != -1, f"unclosed section {match.group(2)}"
        found[f"{match.group(1)}:{match.group(2)}"] = text[match.end():end]
    return found


def code_blocks(section: str) -> list[str]:
    blocks = re.findall(r'<pre class="code[^"]*">(.*?)</pre>', section, re.S | re.I)
    return [norm(re.sub(r"</?code>", "", block)) for block in blocks]


def test_answer_key_exists_and_is_offline():
    assert KEY.is_file(), "answers/answer_key.html is missing"
    text = source()
    assert len(text) > 6000
    lowered = text.lower()
    for needle in ("http://", "https://", "<link", "<img", "<iframe", "@import", "url("):
        assert needle not in lowered, f"answer key is not self-contained: {needle}"
    assert re.search(r"<script", text, re.I) is None


def test_answer_key_is_marked_teacher_only():
    visible = norm(re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", " ", source(), flags=re.S)))
    assert "teacher answer key" in visible.lower()
    assert "do not project" in visible.lower()


def test_answer_key_has_every_section():
    found = sections()
    assert set(found) == {"answer:overview", "answer:create", "answer:boss"} | {
        f"route:{spec.number}" for spec in LEVELS
    }


def test_create_and_boss_code_match_the_game():
    found = sections()
    assert code_blocks(found["answer:create"]) == [norm(mission_one.CREATE_SOLUTION)]
    boss = code_blocks(found["answer:boss"])
    assert boss == [norm(mission_one.BOSS_ROUTE_CODE), norm(mission_one.BOSS_SOLUTION)]


def test_boss_section_shows_the_pad_map_and_guard():
    section = sections()["answer:boss"]
    maps = [norm(block) for block in re.findall(r'<pre class="map">(.*?)</pre>', section, re.S)]
    assert maps == [norm(mission_one.BOSS_MAZE_ASCII)]
    visible = norm(re.sub(r"<[^>]+>", " ", section))
    assert "attack pad" in visible.lower()
    assert "coins >= 30" in visible
    assert "20 steps" in visible


def test_every_level_route_matches_the_game():
    found = sections()
    for spec in LEVELS:
        section = found[f"route:{spec.number}"]
        blocks = code_blocks(section)
        assert blocks[0] == norm(spec.reference_code), f"L{spec.number} code drifted"
        if spec.number == 2:
            assert len(blocks) == 2, "L2 should show the optional chest detour"
            assert blocks[1] == norm(mission_one.L2_CHEST_DETOUR)
        else:
            assert len(blocks) == 1


def test_every_level_shows_its_own_map_and_economy():
    found = sections()
    for spec in LEVELS:
        section = norm(re.sub(r"<[^>]+>", " ", found[f"route:{spec.number}"]))
        assert spec.name in section
        assert f"{spec.start_coins} coins" in section
        assert f"{spec.shortest_steps} steps" in section
        assert f"{spec.expected_steps} steps" in section
        assert f"{spec.expected_coins} coins" in section
        map_blocks = [norm(block) for block in re.findall(r'<pre class="map">(.*?)</pre>', found[f"route:{spec.number}"], re.S)]
        assert map_blocks == [norm(spec.maze_ascii)]


def test_answer_key_explains_the_economy():
    visible = norm(re.sub(r"<[^>]+>", " ", source()))
    assert "+10" in visible and "+20" in visible
    assert str(C.FINAL_BONUS_TARGET) in visible
    assert "bonus" in visible.lower()
    assert "chest detour" in visible.lower()
    assert str(C.PRACTICE_COINS) in visible, "practice run coin count missing"


def test_overview_table_covers_the_campaign():
    overview = sections()["answer:overview"]
    rows = re.findall(r"<tr>(.*?)</tr>", overview, re.S | re.I)
    body = [row for row in rows if "<td" in row]
    assert len(body) == len(LEVELS)
    for row, spec in zip(body, LEVELS):
        cells = [norm(cell) for cell in re.findall(r"<td>(.*?)</td>", row, re.S)]
        assert cells[1] == spec.name
        assert cells[2] == str(spec.start_coins)
        assert cells[3] == str(spec.shortest_steps)
        assert cells[5] == str(spec.expected_steps)
        assert cells[6] == str(spec.expected_coins)
