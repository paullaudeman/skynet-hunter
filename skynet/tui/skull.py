"""A multi-colour pixel T-800, rendered in the terminal via the half-block trick.

Each character cell is a "▀": its FOREGROUND colour is the top pixel, its
BACKGROUND colour is the bottom pixel. So one text cell encodes two stacked
square pixels with independent colour ~ double vertical density, full colour.
This is how terminal image viewers (chafa, jp2a) reach photographic fidelity,
and it's why "ASCII can't do this" was wrong: monochrome was the limit, not ASCII.

Same pixel map as docs/explainer.html ~ keep them in sync if you tune the art.
"""

from __future__ import annotations

from rich.style import Style
from rich.text import Text

BG = "#0a0706"

SKULL = [
    "......bBBBBb......",
    "....bBGGGGGGBb....",
    "...bGwwwwwwwwGb...",
    "..bGwwwGGGGwwwGb..",
    ".bGwwGGggggGGwwGb.",
    ".bGwGGgddddggGwGb.",
    "bGwGgdkkkddkdgGwGb",
    "bGGgddkkkkkkddgGGb",
    "bGgdkkRxkkxRkkdgGb",
    "bGgdkkRxkkxRkkdgGb",
    "bGGgdkkkddkkkdgGGb",
    ".bGggdkkddkkdggGb.",
    ".bGGggddddddggGGb.",
    "..bGGgggkkgggGGb..",
    "..bGGGgdkkdgGGGb..",
    "...bGGgdkkdgGGb...",
    "...bGGggddggGGb...",
    "..bGGgyYYYYygGGb..",
    "..bGggyyyyyyggGb..",
    "...bGGgddddgGGb...",
    "....bGGddddGGb....",
    ".....bGGGGGGb.....",
    "......bgddgb......",
    ".......bggb.......",
]

PAL = {
    "b": "#4f80a4", "B": "#8fc0dd", "w": "#e8edf2", "G": "#a7adb8",
    "g": "#767c88", "d": "#454b5c", "k": "#20242e", "r": "#b8331e",
    "R": "#ff4d2c", "x": "#ffffff", "y": "#bd9f36", "Y": "#edcb60",
}


def skull_text() -> Text:
    """Render the skull as a centered Rich Text using half-blocks."""
    t = Text(justify="center")
    width = len(SKULL[0])
    for r in range(0, len(SKULL), 2):
        top = SKULL[r]
        bot = SKULL[r + 1] if r + 1 < len(SKULL) else "." * width
        for c in range(width):
            top_c = PAL.get(top[c], BG)
            bot_c = PAL.get(bot[c], BG)
            t.append("▀", style=Style(color=top_c, bgcolor=bot_c))
        t.append("\n")
    return t
