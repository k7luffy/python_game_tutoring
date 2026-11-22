"""Cross-checks between the game, the deck, the plan, the README and the key.

These tests are deliberately dependency-free: they read the delivered documents and
the game's mission data, so they catch drift such as a slide-count change, a renamed
command, a moved level or an answer route leaking into the deck.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

from missions import mission_one

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides" / "index.html"
PLAN = ROOT / "lesson_plan" / "lesson_plan.md"
README = ROOT / "README.md"
ANSWER_KEY = ROOT / "answers" / "answer_key.html"
GAME_MAIN = ROOT / "game" / "main.py"
CONSTANTS = ROOT / "game" / "engine" / "constants.py"
LAUNCHER_MAC = ROOT / "run_game.command"
LAUNCHER_WIN = ROOT / "run_game.bat"

EXPECTED_TITLES = [
    "Python Maze Adventure: The Coin Mission",
    "Today's Mission",
    "Quick Revision – Variables",
    "Quick Revision – Comparison Operators",
    "Quick Revision – If-else",
    "Review Quiz",
    "Asking for Input with input()",
    "Turning Text into Numbers with int()",
    "Putting Input Together",
    "Input Quiz",
    "Why Loops? The Copy-Paste Problem",
    "Introducing for and range()",
    "Tracing a for Loop",
    "Your First Game Loop",
    "For Loop Quiz",
    "What Is a Function?",
    "Defining and Calling a Function",
    "Adding Parameters to Functions",
    "Building move_right(steps)",
    "Function Quiz",
    "Meet the Game",
    "The Maze – Four Levels, One Budget",
    "Lesson Review",
    "Exit Ticket",
]

EXPECTED_REFS = [(1, 2), (3, 6), (7, 10), (11, 15), (16, 20), (21, 22), (23, 24)]
QUIZ_SLIDES = {6, 10, 15, 20}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def _visible(fragment: str) -> str:
    fragment = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<style\b.*?</style>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return _norm(fragment)


def _slide_chunks(source: str) -> list[tuple[str, str]]:
    starts = list(re.finditer(r"<section\b[^>]*>", source))
    chunks: list[tuple[str, str]] = []
    for i, match in enumerate(starts):
        if i + 1 < len(starts):
            end = starts[i + 1].start()
        else:
            end = source.find("</section>", match.end())
            if end == -1:
                end = len(source)
        chunks.append((match.group(0), source[match.start():end]))
    return chunks


def _stage_titles() -> list[str]:
    source = _read(CONSTANTS)
    block = re.search(r"STAGE_TITLES\s*=\s*\{(.*?)\}", source, re.S)
    assert block is not None, "STAGE_TITLES not found in constants.py"
    return re.findall(r'"([^"]+)"', block.group(1))


def _reference_routes() -> list[str]:
    return [spec.reference_code for spec in mission_one.LEVELS] + [mission_one.L2_CHEST_DETOUR]


def test_deliverables_exist() -> None:
    for path in (
        SLIDES, PLAN, README, ANSWER_KEY, GAME_MAIN, CONSTANTS, LAUNCHER_MAC, LAUNCHER_WIN
    ):
        assert path.is_file(), f"missing deliverable: {path}"
    assert os.access(LAUNCHER_MAC, os.X_OK), "run_game.command is not executable"


def test_exactly_twenty_four_slides() -> None:
    source = _read(SLIDES)
    chunks = _slide_chunks(source)
    assert len(chunks) == 24, f"the deck must contain exactly 24 slides, found {len(chunks)}"
    ids = []
    for opening, _ in chunks:
        match = re.search(r'id="slide-(\d+)"', opening)
        assert match is not None, opening
        ids.append(int(match.group(1)))
        classes = re.search(r'class="([^"]*)"', opening)
        assert classes is not None and "slide" in classes.group(1).split()
    assert ids == list(range(1, 25)), "slide ids must run from slide-1 to slide-24 in order"
    assert source.count("1 / 24") >= 1, "the counter must start at 1 / 24"


def test_slide_titles_match_the_brief() -> None:
    chunks = _slide_chunks(_read(SLIDES))
    for (_, chunk), expected in zip(chunks, EXPECTED_TITLES):
        heading = re.search(r"<h[12][^>]*>(.*?)</h[12]>", chunk, re.S | re.I)
        assert heading is not None, f"no heading in slide starting {chunk[:70]!r}"
        assert _norm(_visible(heading.group(1))) == _norm(expected)


def test_every_slide_has_presenter_notes() -> None:
    for _, chunk in _slide_chunks(_read(SLIDES)):
        notes = re.findall(r'<aside class="notes"[^>]*>(.*?)</aside>', chunk, re.S | re.I)
        assert len(notes) == 1, "each slide needs exactly one presenter-notes block"
        assert len(_visible(notes[0])) >= 40, "presenter notes are too short"


def test_quizzes_are_interactive_and_on_the_four_quiz_slides() -> None:
    chunks = _slide_chunks(_read(SLIDES))
    per_slide = []
    for number, (_, chunk) in enumerate(chunks, start=1):
        quizzes = re.findall(r'<div class="quiz" data-answer="([a-c])">(.*?)</div>\s*(?=<div class="quiz"|</div>)', chunk, re.S)
        counts = chunk.count('<div class="quiz"')
        per_slide.append((number, counts, quizzes))
    assert sum(c for _, c, _ in per_slide) == 12, "the deck must contain twelve quizzes"
    for number, count, quizzes in per_slide:
        assert count == (3 if number in QUIZ_SLIDES else 0), f"slide {number} has the wrong quiz count"
    for number, _, quizzes in per_slide:
        if number not in QUIZ_SLIDES:
            continue
        assert len(quizzes) == 3
        for answer, body in quizzes:
            options = re.findall(r'data-opt="([a-c])"', body)
            assert options == ["a", "b", "c"], "each quiz needs options A, B and C"
            assert answer in options
            assert 'class="q-feedback"' in body
            assert 'class="q-explain"' in body
            assert 'class="q-reset"' in body


def test_quiz_javascript_hooks_are_present() -> None:
    source = _read(SLIDES)
    for needle in (
        "function initQuizzes",
        "function resetAllQuizzes",
        'closest(".quiz")',
        "inQuiz",
        ".q-explain",
        'k === "r" || k === "R"',
    ):
        assert needle in source, f"quiz hook missing: {needle}"
    assert "initQuizzes();" in source


def test_deck_is_self_contained() -> None:
    source = _read(SLIDES)
    lowered = source.lower()
    assert "http://" not in lowered and "https://" not in lowered
    for needle in ("<link", "<img", "<iframe", "@import", "url("):
        assert needle not in lowered, f"external reference found: {needle}"
    assert re.search(r"<script[^>]+src\s*=", source, re.I) is None
    assert re.search(r"<script", source, re.I) is not None


def test_coin_values_and_budget_are_consistent() -> None:
    docs = {
        "deck": _visible(_read(SLIDES)),
        "plan": _norm(_read(PLAN)),
        "readme": _norm(_read(README)),
    }
    for name, text in docs.items():
        assert re.search(r"gold\s+coin[^.]{0,60}\+?\s*10", text, re.I), f"gold coin (+10) missing from {name}"
        assert re.search(r"treasure\s+chest[^.]{0,60}\+?\s*20", text, re.I), f"chest (+20) missing from {name}"
        assert re.search(r"coins\s*>=\s*30|at\s+least\s+30\s+coins|30\s+coins\s+or\s+more", text, re.I), f"30-coin threshold missing from {name}"
        assert re.search(r"top[s]?(?:ped|s)?\b[^.]{0,80}\b50\s+coins", text, re.I), f"final top-up to 50 missing from {name}"
    for spec in mission_one.LEVELS:
        for name in ("deck", "plan", "readme"):
            assert spec.name in docs[name], f"{spec.name} missing from {name}"
            assert str(spec.start_coins) in docs[name], f"{spec.name} start coins missing from {name}"


def test_level_names_and_start_coins_are_not_old_values() -> None:
    deck = _visible(_read(SLIDES))
    plan = _norm(_read(PLAN))
    readme = _norm(_read(README))
    for text in (deck, plan, readme):
        assert "50 coins" not in text or "practice" in text.lower()
        assert "19 × 13" not in text and "19x13" not in text
    for old in ("21-slide", "26 steps", "34 coins", "46 coins"):
        assert old not in deck and old not in plan and old not in readme


def test_api_names_and_messages_match() -> None:
    deck = _visible(_read(SLIDES))
    plan = _norm(_read(PLAN))
    for text in (deck, plan):
        for name in (
            "move_one_step_up()",
            "move_one_step_down()",
            "move_one_step_left()",
            "move_one_step_right()",
            "fire_super_attack()",
        ):
            assert name in text, f"game command missing from a product: {name}"
        for name in ("turn_left()", "turn_right()", "move_one_step()"):
            assert name not in text, f"old game command still in a product: {name}"
        for name in ("coins", "player_name", "weapon_power"):
            assert name in text, f"game value missing from a product: {name}"
        assert "Super Attack Activated!" in text
        assert "Not enough coins!" in text
    assert "input(" in deck and "int(" in deck
    assert "for i in range(" in deck
    assert "def move_right(steps):" in deck
    assert "def move_forward" not in deck


def test_stage_titles_match_the_game() -> None:
    deck = _visible(_read(SLIDES))
    plan = _norm(_read(PLAN))
    readme = _norm(_read(README))
    titles = _stage_titles()
    assert titles == ["Create Your Explorer", "Escape the Maze", "Super Attack"]
    for title in titles:
        assert title in deck, f"stage title missing from slides: {title}"
        assert title in plan, f"stage title missing from lesson plan: {title}"
        assert title in readme, f"stage title missing from README: {title}"


def test_lesson_plan_slide_references_match_the_deck() -> None:
    plan = _read(PLAN)
    refs = []
    for match in re.finditer(r"(?m)^\*\*Slides?\s+(\d+)(?:\s*[-–—]\s*(\d+))?\*\*\s*$", plan):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        refs.append((start, end))
    assert refs == EXPECTED_REFS, f"lesson-plan slide sections drifted: {refs}"
    for number in re.findall(r"\bslides?\s+(\d+)", plan, re.I):
        assert 1 <= int(number) <= 24, f"slide reference outside 1-24: {number}"
    for old in ("Slides 12–13", "**Slide 14**", "No dedicated slide"):
        assert old not in plan, f"old slide structure still present: {old}"


def test_lesson_plan_matches_game_window_and_controls() -> None:
    plan = _read(PLAN)
    assert "1280 × 800" in plan, "lesson plan must use the real initial window size"
    assert "1440 × 900" not in plan, "the 1440x900 design canvas is not the window size"
    assert "comparison operators" in plan, "revision section must match slides 3-6"
    assert "**Sound**" in plan and "**Muted**" in plan, "sound control wording must match the game"
    assert "Hint" in plan and "empty editor" in plan.lower()


def test_readme_documents_launchers_entry_point_and_answer_key() -> None:
    readme = _read(README)
    for needle in (
        "run_game.command",
        "run_game.bat",
        "game/main.py",
        "slides/index.html",
        "answers/answer_key.html",
        "tools/build_answer_key.py",
        "python -m pytest tests/ -q",
    ):
        assert needle in readme, f"README does not mention {needle}"


def test_slides_do_not_teach_banned_concepts() -> None:
    source = _read(SLIDES)
    blocks = re.findall(r"<pre[^>]*>(.*?)</pre>", source, re.S | re.I)
    assert blocks, "no code blocks found in the deck"
    for block in blocks:
        text = _visible(block)
        for word in ("while", "global", "return", "class", "import", "lambda"):
            assert re.search(rf"\b{word}\b", text, re.I) is None, f"banned word {word!r} in code: {text!r}"
        for char in "[]{}":
            assert char not in text, f"banned character {char!r} in code: {text!r}"


def test_no_answer_routes_leak_outside_the_answer_key() -> None:
    public = {
        "deck": _norm(_visible(_read(SLIDES))),
        "plan": _norm(_read(PLAN)),
        "readme": _norm(_read(README)),
    }
    for name, text in public.items():
        for route in _reference_routes():
            assert _norm(route) not in text, f"a full reference route leaked into {name}"
        assert "def super_attack" not in text, f"the boss answer leaked into {name}"
        assert "for i in range(16):" not in text, f"a level route fragment leaked into {name}"
