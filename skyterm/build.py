#!/usr/bin/env python3
"""Generate the skyterm terminal theme from the Skynet-Hunter amber palette.

Emits an iTerm2 color preset and a Ghostty config. Amber-phosphor monochrome with
two functional accents kept (green for added/success, a burnt red for errors/diffs)
so the theme stays daily-usable. Palette matches web/index.html.

    python3 skyterm/build.py
"""
from __future__ import annotations
import os

NAME = "skyterm"
HERE = os.path.dirname(os.path.abspath(__file__))

BG       = "160d03"  # glowing dark-amber ground (never pure black)
FG       = "ffb43c"  # amber phosphor
CURSOR   = "ffb43c"
CUR_TEXT = "160d03"
SEL_BG   = "3a2a12"
SEL_FG   = "ffd98a"

# 16 ANSI ~ amber ramp, with green (2/10) and burnt-red (1/9) held as accents
ANSI = [
    "160d03",  # 0  black
    "c0531c",  # 1  red    ~ burnt amber
    "7df06a",  # 2  green  ~ phosphor accent (added / success)
    "ffb43c",  # 3  yellow ~ amber (the main)
    "c0801f",  # 4  blue   -> amber-dim (no blue, by preference)
    "e09228",  # 5  magenta-> amber2
    "d9a441",  # 6  cyan   -> amber-light
    "e6cfa0",  # 7  white  ~ pale amber
    "5c3c10",  # 8  bright black ~ faint amber
    "d9632a",  # 9  bright red
    "9bf58a",  # 10 bright green
    "ffc864",  # 11 bright yellow ~ bright amber
    "d9a040",  # 12 bright blue   -> amber
    "f0a838",  # 13 bright magenta-> amber
    "f0c060",  # 14 bright cyan   -> amber
    "fff0d0",  # 15 bright white
]


def floats(hexstr: str) -> tuple[float, float, float]:
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def iterm_color(r: float, g: float, b: float) -> str:
    return (
        "\t<dict>\n"
        "\t\t<key>Color Space</key>\n\t\t<string>sRGB</string>\n"
        f"\t\t<key>Red Component</key>\n\t\t<real>{r:.6f}</real>\n"
        f"\t\t<key>Green Component</key>\n\t\t<real>{g:.6f}</real>\n"
        f"\t\t<key>Blue Component</key>\n\t\t<real>{b:.6f}</real>\n"
        "\t\t<key>Alpha Component</key>\n\t\t<real>1</real>\n"
        "\t</dict>"
    )


def build_itermcolors() -> str:
    rows = []
    for i, hx in enumerate(ANSI):
        rows.append(f"\t<key>Ansi {i} Color</key>\n{iterm_color(*floats(hx))}")
    extra = {
        "Background Color": BG, "Foreground Color": FG,
        "Cursor Color": CURSOR, "Cursor Text Color": CUR_TEXT,
        "Bold Color": FG, "Selection Color": SEL_BG, "Selected Text Color": SEL_FG,
        "Link Color": ANSI[6], "Cursor Guide Color": SEL_BG,
    }
    for k, hx in extra.items():
        rows.append(f"\t<key>{k}</key>\n{iterm_color(*floats(hx))}")
    body = "\n".join(rows)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n' + body + "\n</dict>\n</plist>\n"
    )


def build_ghostty() -> str:
    lines = [
        "# skyterm ~ amber-phosphor monochrome (Skynet Hunter palette)",
        "# install: cp this to ~/.config/ghostty/config (or `theme = skyterm` if placed in themes/)",
        "",
        f"background = {BG}",
        f"foreground = {FG}",
        f"cursor-color = {CURSOR}",
        f"cursor-text = {CUR_TEXT}",
        f"selection-background = {SEL_BG}",
        f"selection-foreground = {SEL_FG}",
        "cursor-style = block",
        "",
    ]
    for i, hx in enumerate(ANSI):
        lines.append(f"palette = {i}=#{hx}")
    lines += [
        "",
        "# Optional CRT feel (Ghostty supports GLSL custom shaders):",
        "#   custom-shader = ~/.config/ghostty/shaders/crt.glsl",
        "#   custom-shader-animation = true",
        "# Find a CRT/retro GLSL shader and drop it in; dial it subtle for daily use.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    with open(os.path.join(HERE, "skyterm.itermcolors"), "w") as f:
        f.write(build_itermcolors())
    os.makedirs(os.path.join(HERE, "ghostty"), exist_ok=True)
    with open(os.path.join(HERE, "ghostty", "skyterm"), "w") as f:
        f.write(build_ghostty())
    print("wrote skyterm.itermcolors + ghostty/skyterm")


if __name__ == "__main__":
    main()
