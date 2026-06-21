"""Palette + Textual CSS for the TUI ~ the same CRT-red Terminator look as the
HTML explainer. Multi-pane HUD: one bezel-framed column per agent."""

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
/* CRT feel: hatch draws faint horizontal scanlines into the background;
   heavy borders read like a monitor bezel; power-on flicker lives in app.py. */
Screen { background: #0a0706; color: #d9cfc9; hatch: horizontal #2a1210 22%; }

#titlebar {
    height: 3;
    content-align: center middle;
    background: #0c0807;
    border: heavy #8e1810;
    color: #ff5141;
    text-style: bold;
}

#body { height: 1fr; }

/* one bezel-framed column per agent ~ the multi-pane HUD */
.agentcol {
    width: 1fr;
    min-width: 24;
    border: heavy #8e1810;
}

.colhdr {
    height: 4;
    padding: 0 1;
    background: #0c0807;
    border-bottom: solid #8e1810;
}

.collog {
    height: 1fr;
    padding: 0 1;
    background: #0d0908;
    scrollbar-color: #8e1810 #0a0706;
}

#sidebar {
    width: 32;
    border: heavy #8e1810;
    hatch: horizontal #1c0c0a 18%;
}

#scenario {
    height: auto;
    padding: 1 1;
    border-bottom: solid #8e1810;
}

#scoreboard {
    height: 1fr;
    padding: 1 1;
}

Footer { background: #150f0d; }
Footer > .footer--key { color: #ff5141; }
"""
