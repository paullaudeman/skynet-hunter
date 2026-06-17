"""Downsample a reference T-800 image into the pixel grid used by the explainer
header AND the TUI banner. This replaces blind hand-authoring with real fidelity.

Usage:
    uv run --with pillow python docs/skull-from-image.py [IMAGE] [WIDTH]

Writes:
    skynet/tui/skull.py        (COLORS grid + half-block render)
    patches docs/explainer.html (the #skull renderer block)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMG = str(ROOT / "docs" / "ref-t800.png")
BG_LUMA = 42  # below this luminance => treat as background (transparent)


def luma(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def build_grid(img_path: str, width: int) -> list[list[str | None]]:
    im = Image.open(img_path).convert("RGB")

    # Auto-crop to the non-black content bounding box.
    mask = im.point(lambda v: 255 if v > BG_LUMA else 0).convert("L")
    bbox = mask.getbbox()
    if bbox:
        pad = 6
        l, t, r, b = bbox
        im = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))

    # Downsample preserving aspect ratio.
    height = max(1, round(width * im.height / im.width))
    im = im.resize((width, height), Image.LANCZOS)

    grid: list[list[str | None]] = []
    for y in range(height):
        row: list[str | None] = []
        for x in range(width):
            r, g, b = im.getpixel((x, y))
            if luma(r, g, b) < BG_LUMA:
                row.append(None)
            else:
                row.append(f"#{r:02x}{g:02x}{b:02x}")
        grid.append(row)
    return grid


def write_tui(grid: list[list[str | None]]) -> None:
    colors_repr = "[\n" + ",\n".join("    " + repr(row) for row in grid) + ",\n]"
    module = '''"""Multi-colour pixel T-800 for the terminal ~ downsampled from a reference
image by docs/skull-from-image.py, rendered via the half-block (▀) trick:
foreground = top pixel, background = bottom pixel => two square full-colour
pixels per cell. Regenerate with that script; don't hand-edit COLORS.
"""

from __future__ import annotations

from rich.style import Style
from rich.text import Text

BG = "#0a0706"

COLORS = __COLORS__


def skull_text() -> Text:
    t = Text(justify="center")
    rows = COLORS
    width = len(rows[0]) if rows else 0
    for r in range(0, len(rows), 2):
        top = rows[r]
        bot = rows[r + 1] if r + 1 < len(rows) else [None] * width
        for c in range(width):
            tc = top[c] or BG
            bc = bot[c] or BG
            t.append("▀", style=Style(color=tc, bgcolor=bc))
        t.append("\\n")
    return t
'''
    module = module.replace("__COLORS__", colors_repr)
    (ROOT / "skynet" / "tui" / "skull.py").write_text(module, encoding="utf-8")
    print("wrote skynet/tui/skull.py")


def patch_html(grid: list[list[str | None]]) -> None:
    html_path = ROOT / "docs" / "explainer.html"
    html = html_path.read_text(encoding="utf-8")
    data = json.dumps(grid)
    block = (
        "// T-800 skull ~ downsampled from a reference image (docs/skull-from-image.py).\n"
        "(function(){\n"
        f"  const C={data};\n"
        "  const el=document.getElementById('skull'); if(!el) return;\n"
        "  const W=C[0].length;\n"
        "  el.style.gridTemplateColumns='repeat('+W+', var(--px))';\n"
        "  function isEye(h){const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return r>185&&(r-b)>45&&(g-b)>28;}\n"
        "  const frag=document.createDocumentFragment();\n"
        "  for(const row of C){for(const c of row){const d=document.createElement('div');d.className='px';if(c){d.style.background=c;if(isEye(c))d.classList.add('eye');}frag.appendChild(d);}}\n"
        "  el.appendChild(frag);\n"
        "})();"
    )
    import re
    # Replace whichever existing skull IIFE is present (hand-map or prior image build).
    pattern = re.compile(r"// (?:Multi-colour pixel T-800|T-800 skull)[\s\S]*?\}\)\(\);")
    if not pattern.search(html):
        raise SystemExit("Could not find the skull renderer block to patch.")
    html = pattern.sub(lambda _m: block, html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print("patched docs/explainer.html")


def main() -> None:
    img = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMG
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 28
    grid = build_grid(img, width)
    print(f"grid: {len(grid[0])} x {len(grid)}  (TUI lines: {(len(grid) + 1) // 2})")
    write_tui(grid)
    patch_html(grid)


if __name__ == "__main__":
    main()
