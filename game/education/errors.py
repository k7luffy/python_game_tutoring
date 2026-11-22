"""Turn Python errors into friendly, child-sized explanations."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

GAME_FUNCTIONS = [
    "move_one_step_up",
    "move_one_step_down",
    "move_one_step_left",
    "move_one_step_right",
    "fire_super_attack",
    "input",
    "print",
]

GAME_NAMES = GAME_FUNCTIONS + [
    "coins",
    "player_name",
    "weapon_power",
    "range",
    "int",
    "str",
    "float",
    "bool",
    "len",
    "abs",
    "round",
    "min",
    "max",
    "sum",
    "True",
    "False",
    "None",
]


@dataclass
class ErrorCard:
    """A ready-to-display explanation of a problem in student code."""

    title: str
    message: str
    hint: str = ""
    line_number: int | None = None
    code_line: str = ""
    caret: str = ""

    def console_lines(self) -> list[str]:
        lines = [f"{self.title}: {self.message}"]
        if self.code_line:
            prefix = f"Line {self.line_number}: " if self.line_number else "  "
            lines.append(f"{prefix}{self.code_line}")
            if self.caret:
                lines.append(" " * len(prefix) + self.caret)
        if self.hint:
            lines.append(f"Tip: {self.hint}")
        return lines


def _source_line(source: str, number: int | None) -> str:
    if not number or number < 1:
        return ""
    lines = source.splitlines()
    if number <= len(lines):
        return lines[number - 1].rstrip()
    return ""


def _defined_names(source: str) -> list[str]:
    names = set(re.findall(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)", source))
    names.update(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", source, re.MULTILINE))
    return sorted(names)


def _suggest(name: str, source: str, extra: list[str] | None = None) -> str:
    candidates = GAME_NAMES + _defined_names(source) + list(extra or [])
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.72)
    return matches[0] if matches else ""


def syntax_error_card(exc: SyntaxError, source: str) -> ErrorCard:
    line = exc.lineno
    text = (exc.text or "").rstrip("\n") or _source_line(source, line)
    offset = exc.offset or 0
    caret = ""
    if text:
        width = max(1, (exc.end_offset or offset) - offset) if offset else 1
        caret = " " * max(0, offset - 1) + "^" * width
    title = "Syntax Error"
    message = "Python could not read this line. Something is missing or spelled wrongly."
    hint = "Check for a missing bracket, quote or colon (:)."
    raw = (exc.msg or "").lower()
    if "expected ':'" in raw:
        message = "A colon (:) is missing at the end of this line."
        hint = "Lines that start with def, if, else or for finish with a colon."
    elif "unexpected indent" in raw:
        title = "Indentation Error"
        message = "This line is indented (pushed in) but it should not be."
        hint = "Only lines inside a def, if or for block are pushed in by 4 spaces."
    elif "expected an indented block" in raw:
        title = "Indentation Error"
        message = "Python expected an indented line after this one."
        hint = "Push the next line in by 4 spaces."
    elif "unindent does not match" in raw or "inconsistent use of tabs" in raw:
        title = "Indentation Error"
        message = "The indentation does not line up with the block above."
        hint = "Use the same 4 spaces as the other lines in the block."
    elif "was never closed" in raw or "unexpected eof" in raw:
        message = "A bracket or quote was opened but never closed."
        hint = "Every ( needs a ) and every ' needs a '."
    elif "invalid syntax" in raw:
        hint = "Look for a missing quote, bracket or comma near the caret."
    return ErrorCard(title, message, hint, line, text, caret)


def _error_line(exc: BaseException, source: str) -> int | None:
    line = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<student>":
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def runtime_error_card(
    exc: BaseException,
    source: str,
    line: int | None = None,
) -> ErrorCard:
    line = line or _error_line(exc, source)
    text = _source_line(source, line)
    name = type(exc).__name__
    detail = str(exc)

    if isinstance(exc, NameError):
        missing = re.search(r"name '([^']+)'", detail)
        missing_name = missing.group(1) if missing else ""
        if missing_name == "input":
            return ErrorCard(
                "Input Error",
                "input() was not used correctly.",
                "Write input(\"Question? \") to ask the player something.",
                line,
                text,
            )
        suggestion = _suggest(missing_name, source)
        message = f"Python does not know the name '{missing_name}'."
        if suggestion:
            hint = f"Did you mean '{suggestion}'? Check your spelling."
        elif missing_name.lower().startswith(("move", "turn", "step", "walk", "go")):
            hint = (
                "The moves are move_one_step_up(), move_one_step_down(), "
                "move_one_step_left() and move_one_step_right()."
            )
        elif missing_name.lower().startswith(("fire", "attack", "super")):
            hint = "The attack command is fire_super_attack(). Check the spelling."
        else:
            hint = (
                "Check the spelling, or create the variable before you use it. "
                "For example: score = 5"
            )
        return ErrorCard("Name Error", message, hint, line, text)

    if isinstance(exc, ValueError) and ("int" in detail or "literal" in detail):
        found = detail.replace("invalid literal for int() with base 10:", "").strip()
        return ErrorCard(
            "Value Error",
            "int() could not turn that text into a whole number.",
            "Type digits only, like 7. If you typed letters, try again with a number.",
            line,
            text,
        )

    if isinstance(exc, IndentationError):
        return syntax_error_card(exc, source)  # type: ignore[arg-type]

    if isinstance(exc, TypeError):
        if "positional argument" in detail and "move_one_step" in detail:
            return ErrorCard(
                "Argument Error",
                "A move_one_step_ command moves exactly one step and takes no numbers.",
                "To move several steps, repeat it in a for loop or make your own function.",
                line,
                text,
            )
        if "positional argument" in detail and "fire_super_attack" in detail:
            return ErrorCard(
                "Argument Error",
                "fire_super_attack() does not need any arguments.",
                "Write fire_super_attack() with empty brackets.",
                line,
                text,
            )
        if "unsupported operand" in detail or "can only concatenate" in detail:
            return ErrorCard(
                "Type Error",
                "You tried to do maths with text or join a number and text directly.",
                'Use int() to make a number, and join text with commas in print().',
                line,
                text,
            )
        if "missing" in detail and "argument" in detail:
            return ErrorCard(
                "Argument Error",
                "A function was called without the information it needs.",
                "Check the brackets: input(\"Question? \").",
                line,
                text,
            )
        if "is not callable" in detail:
            return ErrorCard(
                "Type Error",
                "You used brackets on something that is not a function.",
                "Only functions such as move_one_step_right() use brackets.",
                line,
                text,
            )
        return ErrorCard(
            "Type Error",
            "Python received the wrong type of information for this instruction.",
            "Check the numbers and text you passed in.",
            line,
            text,
        )

    if isinstance(exc, ZeroDivisionError):
        return ErrorCard(
            "Maths Error",
            "You cannot divide by zero.",
            "Check the number you are dividing by.",
            line,
            text,
        )

    if isinstance(exc, RecursionError):
        return ErrorCard(
            "Recursion Error",
            "A function kept calling itself and never stopped.",
            "Make sure a function calls a move command, not itself.",
            line,
            text,
        )

    if isinstance(exc, AttributeError):
        return ErrorCard(
            "Attribute Error",
            "That value does not have the part after the dot.",
            "Check the spelling after the dot, or remove it.",
            line,
            text,
        )

    if isinstance(exc, (IndexError, KeyError)):
        return ErrorCard(
            "Index Error",
            "That item does not exist.",
            "Check the number or name inside the square brackets.",
            line,
            text,
        )

    return ErrorCard(
        f"{name}",
        detail or "Something went wrong.",
        "Read the line number, then check that line closely.",
        line,
        text,
    )


def timeout_card(seconds: float) -> ErrorCard:
    return ErrorCard(
        "Time Limit",
        f"Your program took longer than {seconds:.0f} seconds to finish.",
        "A loop might never stop. Check that your loop has a sensible range().",
    )


def fuel_card() -> ErrorCard:
    return ErrorCard(
        "Program Too Long",
        "Your program ran too many instructions and was stopped safely.",
        "Check for a loop that never ends, or a loop with a huge range.",
    )


def action_limit_card(limit: int) -> ErrorCard:
    return ErrorCard(
        "Too Many Moves",
        f"Your program tried more than {limit} actions in one run.",
        "Shorten your route or use a for loop instead of many single steps.",
    )


def cancelled_card() -> ErrorCard:
    return ErrorCard(
        "Program Stopped",
        "You stopped the program.",
        "Press Run Code when you are ready to try again.",
    )


def blocked_code_card(reason: str) -> ErrorCard:
    return ErrorCard(
        "Not Allowed",
        reason,
        "This game only lets you use the commands shown in the Help panel.",
    )
