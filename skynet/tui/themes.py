"""Palette + Textual CSS for the TUI ~ the same CRT-red Terminator look as the
HTML explainer. Multi-pane HUD: one bezel-framed column per agent."""

# Per-unit + status colors (hex, for Rich markup in the log).
# Dingy Crystal-Peak bunker CRT ~ faded phosphor, dusted-down, low contrast.
# Identity colors kept but grimed; success-green stays poppy so the win cuts
# through the grime.
PALETTE = {
    "skynet": "#5f97a4",   # blue, dusted
    "t1000": "#b3aa9e",    # silver, grimy
    "t800": "#cf4636",     # red, aged (not neon)
    "blue": "#5f97a4",
    "silver": "#b3aa9e",
    "red": "#cf4636",
    "amber": "#cc9226",    # dusty amber phosphor
    "green": "#4ec257",    # kept bright ~ success should pop
    "dim": "#7d7164",      # grimier dim
    "fg": "#c3b6a2",       # faded phosphor text
    "redhud": "#c2382a",   # muted hud red
}

STATUS_GLYPH = {"idle": "○", "thinking": "◉", "deployed": "●"}
UNIT_GLYPH = {"skynet": "◤", "t1000": "❖", "t800": "⚙"}

CSS = """
/* CRT feel: hatch draws faint horizontal scanlines into the background;
   heavy borders read like a monitor bezel; power-on flicker lives in app.py. */
/* dingy bunker tube: warm near-black, dusty (not red) scanlines, grimy aged cast */
Screen { background: #0b0908; color: #c3b6a2; hatch: horizontal #2a2418 44%; tint: #46381f 17%; }

#titlebar {
    height: 3;
    content-align: center middle;
    background: #0c0807;
    border: heavy #5e3024;
    color: #ff5141;
    text-style: bold;
}

#body { height: 1fr; }

/* one bezel-framed column per agent ~ the multi-pane HUD */
.agentcol {
    width: 1fr;
    min-width: 24;
    border: heavy #5e3024;
}

.colhdr {
    height: 4;
    padding: 0 1;
    background: #0c0807;
    border-bottom: solid #5e3024;
}

/* success flash ~ the winning unit's pane OUTLINE + header blink green a few times */
.agentcol.flash {
    border: heavy #3fcf5a;
}
.agentcol.flash .colhdr {
    background: #1d4016;
    border-bottom: solid #3fcf5a;
}

.collog {
    height: 1fr;
    padding: 0 1;
    background: #0d0908;
    hatch: horizontal #34160f 38%;
    scrollbar-color: #5e3024 #0a0706;
}

#sidebar {
    width: 32;
    border: heavy #5e3024;
    hatch: horizontal #34160f 38%;
}

#scenario {
    height: auto;
    padding: 1 1;
    border-bottom: solid #5e3024;
}

#scoreboard {
    height: 1fr;
    padding: 1 1;
}

/* scrolling intel ticker ~ amber CRT phosphor, scanlined (no border: a heavy
   border is a full row and would eat the ticker's only line) */
#ticker {
    height: 1;
    background: #160a08;
    color: #e0a030;
    hatch: horizontal #2a1410 30%;
    text-style: bold;
}

Footer { background: #150f0d; }
Footer > .footer--key { color: #ff5141; }
"""
