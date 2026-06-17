"""Palette + Textual CSS for the TUI ~ the same CRT-red Terminator look as the
HTML explainer."""

# Per-unit + status colors (hex, for Rich markup in the log).
PALETTE = {
    "skynet": "#6fb0c0",   # blue
    "t1000": "#cfc6bf",    # silver
    "t800": "#ff5141",     # red
    "blue": "#6fb0c0",
    "silver": "#cfc6bf",
    "red": "#ff5141",
    "amber": "#ffb000",
    "green": "#3fcf5a",
    "dim": "#9a8c84",
    "fg": "#d9cfc9",
    "redhud": "#ff2d20",
}

STATUS_GLYPH = {"idle": "○", "thinking": "◉", "deployed": "●"}
UNIT_GLYPH = {"skynet": "◤", "t1000": "❖", "t800": "⚙"}

CSS = """
Screen { background: #0a0706; color: #d9cfc9; }

#titlebar {
    height: 3;
    content-align: center middle;
    background: #0c0807;
    border: round #8e1810;
    color: #ff5141;
    text-style: bold;
}

#body { height: 1fr; }

#units {
    width: 28;
    border: round #8e1810;
    padding: 1 1;
}

#log {
    width: 1fr;
    border: round #8e1810;
    background: #0d0908;
    padding: 0 1;
    scrollbar-color: #8e1810 #0a0706;
}

#scenario {
    width: 34;
    border: round #8e1810;
    padding: 1 1;
}

Footer { background: #150f0d; }
Footer > .footer--key { color: #ff5141; }
"""
