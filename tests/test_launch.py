"""The Windows and macOS launch paths stay runnable.

These checks pin the fixes that keep the game opening on a school laptop:

* ``run_game.bat`` must use CRLF line endings.  With bare LF endings cmd.exe
  reports "The system cannot find the batch label specified" at ``goto``.
* The batch file must use a Python that already has pygame (in the project
  environment or on the system) before building a new one, must find an
  interpreter whether the machine exposes ``py -3``, ``python`` or ``python3``,
  and must not close its window on failure.
* The game must set the Windows DPI hints before pygame starts, so display
  scaling does not blur or shrink the window, and must guard its console
  encoding so a legacy code page cannot stop it opening.
"""

from __future__ import annotations

import os
import re

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN_LAUNCHER = ROOT / "run_game.bat"
MAC_LAUNCHER = ROOT / "run_game.command"
GAME_MAIN = ROOT / "game" / "main.py"


def test_windows_launcher_uses_crlf_and_stays_ascii():
    raw = WIN_LAUNCHER.read_bytes()
    assert raw, "run_game.bat is empty"
    assert all(byte < 128 for byte in raw), "keep run_game.bat ASCII for cmd.exe"
    assert b"\x00" not in raw
    lines = raw.split(b"\n")
    assert lines[-1] == b"", "run_game.bat should end with a newline"
    for number, line in enumerate(lines[:-1], start=1):
        assert line.endswith(b"\r"), f"run_game.bat line {number} is not CRLF"
    assert raw.count(b"\r\n") == len(lines) - 1


def test_windows_launcher_finds_python_and_the_entry_point():
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    for needle in (
        r".venv\Scripts\python.exe",
        r"game\main.py",
        r"game\requirements.txt",
        "py -3",
        "python3",
        "goto setup_error",
        "goto game_error",
        "PYTHONUTF8=1",
        "pause",
        'rmdir /s /q ".venv"',
    ):
        assert needle in text, f"run_game.bat lost {needle!r}"
    assert text.count("@echo off") == 1


def test_windows_launcher_goto_labels_all_exist():
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    labels = set(re.findall(r"^:([A-Za-z0-9_]+)", text, re.MULTILINE))
    targets = set(re.findall(r"^\s*goto\s+([A-Za-z0-9_]+)", text, re.MULTILINE | re.IGNORECASE))
    assert labels, "run_game.bat has no labels to jump to"
    assert targets <= labels, f"goto without a label: {sorted(targets - labels)}"


def test_windows_launcher_tries_each_interpreter_name():
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    order = [text.index("py -3 -c"), text.index("python -c"), text.index("python3 -c")]
    assert order == sorted(order), "try py -3, then python, then python3"
    assert "sys.version_info >= (3, 10)" in text


def test_windows_launcher_reuses_a_python_that_already_has_pygame():
    """A machine with pygame installed must not need a new virtual environment."""
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    venv_probe = text.index('"%PY%" -c "import pygame"')
    system_probe = text.index('py -3 -c "import pygame"')
    make_venv = text.index(":make_venv")
    assert venv_probe < make_venv, "check the project environment before building one"
    assert system_probe < make_venv, "check the installed Pythons before building one"
    assert text.index("goto try_py") < system_probe
    assert "%BASE% game\\main.py" in text, "the system Python must start the game"
    assert "import pygame" in text[text.index(":have_python"):], (
        "after installing, prove that pygame imports"
    )


def test_windows_launcher_repairs_a_broken_environment():
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    assert ":repair" in text and ":rebuild" in text
    repair = text.index(":repair")
    rebuild = text.index(":rebuild")
    assert repair < rebuild
    assert 'rmdir /s /q ".venv"' in text[rebuild - 200:rebuild + 200]


def test_windows_launcher_explains_a_failed_install():
    text = WIN_LAUNCHER.read_text(encoding="ascii")
    assert ":install_error" in text
    assert 'sys.version.split()[0]' in text, "show the Python version that failed"
    assert "Python 3.12 or 3.13" in text


def test_entry_point_explains_a_missing_pygame():
    text = GAME_MAIN.read_text(encoding="utf-8")
    assert "except ModuleNotFoundError" in text
    assert "run_game.bat" in text and "run_game.command" in text
    assert "sys.executable" in text


def test_entry_point_keeps_the_console_open_after_a_crash():
    text = GAME_MAIN.read_text(encoding="utf-8")
    assert "def _pause_for_windows" in text
    assert 'os.name != "nt"' in text
    assert "Press Enter to close this window." in text
    assert "traceback.print_exc()" in text
    assert "except KeyboardInterrupt:" in text


def test_main_reports_an_unexpected_crash(monkeypatch, capsys):
    import main as entry

    class BoomApp:
        def run(self) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(entry, "App", BoomApp)
    with pytest.raises(SystemExit) as info:
        entry.main()
    assert info.value.code == 1
    out = capsys.readouterr()
    assert "unexpected error" in out.out
    assert "RuntimeError" in out.err


def test_macos_launcher_stays_lf_and_executable():
    assert MAC_LAUNCHER.is_file()
    assert os.access(MAC_LAUNCHER, os.X_OK), "run_game.command is not executable"
    raw = MAC_LAUNCHER.read_bytes()
    assert b"\r\n" not in raw, "run_game.command should keep Unix line endings"
    assert b".venv/bin/python" in raw


def test_windows_dpi_hints_are_set_before_pygame_imports():
    text = GAME_MAIN.read_text(encoding="utf-8")
    pygame_import = text.index("import pygame")
    for hint in (
        '"PYGAME_HIDE_SUPPORT_PROMPT", "1"',
        '"SDL_WINDOWS_DPI_AWARENESS", "permonitorv2"',
        '"SDL_WINDOWS_DPI_SCALING", "0"',
    ):
        assert hint in text, hint
        assert text.index(hint) < pygame_import, f"{hint} must come before pygame"


def test_entry_point_guards_the_console_encoding():
    text = GAME_MAIN.read_text(encoding="utf-8")
    assert '_ensure_utf8_console' in text
    assert 'reconfigure(encoding="utf-8", errors="replace")' in text
    assert (
        "def main() -> None:\n    _ensure_utf8_console()\n    try:\n        App().run()"
        in text
    )


def test_entry_point_imports_cleanly_with_dummy_video():
    """Importing the entry point must not need a display or a sound device."""
    import subprocess
    import sys

    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    result = subprocess.run(
        [sys.executable, "-c", "import main; print(main.App.__name__)"],
        cwd=ROOT / "game",
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "App" in result.stdout
