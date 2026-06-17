"""ANSI / truecolor theming for the Skynet Hunter terminal.

Raw escape codes, no dependencies ~ the BBS aesthetic deserves the metal.
Palette is muted on purpose (Nord-ish): no flat saturated blue, chrome-grey
for the T-1000, endoskeleton red for the T-800.
"""

from __future__ import annotations

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"


def fg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


# Fixed per-unit identity colors. These never change with the theme ~ they ARE
# the units. blue=Skynet, silver=T-1000, red=T-800, green=Resistance/confirm.
UNIT_RGB: dict[str, tuple[int, int, int]] = {
    "blue": (96, 148, 214),
    "silver": (198, 204, 214),
    "red": (206, 78, 66),
    "green": (120, 200, 140),
}

# Theme = the chrome around the units (frame, headings, status).
THEMES: dict[str, dict[str, tuple[int, int, int]]] = {
    "platinum": {
        "frame": (150, 156, 168),
        "dim": (108, 114, 126),
        "accent": (212, 218, 228),
        "ok": (120, 200, 140),
        "warn": (220, 182, 92),
        "bad": (206, 84, 70),
    },
    "silver": {
        "frame": (122, 128, 140),
        "dim": (88, 94, 106),
        "accent": (190, 196, 208),
        "ok": (120, 200, 140),
        "warn": (220, 182, 92),
        "bad": (206, 84, 70),
    },
    "amber": {
        "frame": (184, 142, 62),
        "dim": (142, 112, 52),
        "accent": (232, 192, 96),
        "ok": (150, 200, 92),
        "warn": (232, 192, 96),
        "bad": (212, 92, 62),
    },
}

_GRADIENT = "░▒▓█▓▒░"


class Theme:
    """Resolves colors for a chosen theme and paints strings."""

    def __init__(self, name: str = "platinum") -> None:
        self.name = name if name in THEMES else "platinum"
        self._c = THEMES[self.name]

    # -- chrome colors --
    def paint(self, key: str, text: str, bold: bool = False) -> str:
        rgb = self._c.get(key) or UNIT_RGB.get(key) or self._c["accent"]
        return f"{BOLD if bold else ''}{fg(rgb)}{text}{RESET}"

    def unit(self, color: str, text: str, bold: bool = False) -> str:
        rgb = UNIT_RGB.get(color, self._c["accent"])
        return f"{BOLD if bold else ''}{fg(rgb)}{text}{RESET}"

    # -- a CP437-style gradient band, BBS scene-release energy --
    def band(self, label: str = "", width: int = 64) -> str:
        edge = _GRADIENT
        core = label.strip()
        if core:
            core = f" {core} "
        pad = max(0, width - 2 * len(edge) - len(core))
        left = pad // 2
        right = pad - left
        line = f"{edge}{'█' * left}{core}{'█' * right}{edge}"
        return self.paint("frame", line, bold=True)
