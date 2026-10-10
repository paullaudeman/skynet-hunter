"""The Judgment Day beat animates only on a real terminal with art on; elsewhere it prints once."""

from __future__ import annotations

from skynet.theme import Theme
from skynet.ui import UI


def test_judgment_day_prints_once_when_not_a_tty(capsys):
    UI(Theme("amber"), art=True).judgment_day('  "Judgment Day is inevitable."')   # capsys is not a tty
    out = capsys.readouterr().out
    assert out.count("Judgment Day is inevitable.") == 1
    assert "\r" not in out


def test_judgment_day_prints_once_with_art_off(capsys):
    UI(Theme("amber"), art=False).judgment_day('  "Judgment Day is inevitable."')
    out = capsys.readouterr().out
    assert out.count("Judgment Day is inevitable.") == 1 and "\r" not in out


def test_hold_returns_at_once_when_not_interactive(capsys):
    """Scripts, pipes and tests must exit: hold() is a no-op without a terminal."""
    ui = UI(Theme("amber"), art=True)
    ui.judgment_day('  "Judgment Day is inevitable."')
    ui.hold()                       # capsys is not a tty: returns immediately
    assert "press any key" not in capsys.readouterr().out
