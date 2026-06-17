"""Generate docs/skull-proofs.html ~ a proof sheet of T-800 skull variations.

Authoring pixel art blind, so this validates every variant is rectangular and
renders them side by side for Paul to pick. Pick one, then we promote its map
into docs/explainer.html + skynet/tui/skull.py.
"""

from pathlib import Path

PAL = {
    "b": "#4f80a4", "B": "#8fc0dd", "w": "#e8edf2", "G": "#a7adb8",
    "g": "#767c88", "d": "#454b5c", "k": "#20242e", "r": "#b8331e",
    "R": "#ff4d2c", "x": "#ffffff", "y": "#bd9f36", "Y": "#edcb60",
}

# Shared upper face (rows 0-16) used by several variants.
TOP = [
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
]

LOWER_BASE = [
    "..bGGgyYYYYygGGb..",
    "..bGggyyyyyyggGb..",
    "...bGGgddddgGGb...",
    "....bGGddddGGb....",
    ".....bGGGGGGb.....",
    "......bgddgb......",
    ".......bggb.......",
]

LOWER_WIDE = [
    ".bGGggyYYYYyggGGb.",
    ".bGgggyyyyyygggGb.",
    ".bGGgggddddgggGGb.",
    "..bGGGddddddGGGb..",
    "..bGGGGddddGGGGb..",
    "...bGGGGGGGGGGb...",
    "....bGGGGGGGGb....",
]

LOWER_GRIN = [
    ".bGgyYYYYYYYYygGb.",
    ".bGggyYYYYYYyggGb.",
    ".bGGgyyyyyyyygGGb.",
    "..bGGggddddggGGb..",
    "..bGGgddddddgGGb..",
    "...bGGgddddgGGb...",
    "....bGGddddGGb....",
]

# Full narrow/gaunt variant.
NARROW = [
    ".......bBBb.......",
    ".....bBGGGGBb.....",
    "....bGwwwwwwGb....",
    "...bGwwGGGGwwGb...",
    "..bGwGgddddgGwGb..",
    "..bGwGdkkkkdGwGb..",
    "..bGGgdkkkkdgGGb..",
    "..bGgdkRxxRkdgGb..",
    "..bGgdkRxxRkdgGb..",
    "..bGGgdkkkkdgGGb..",
    "...bGgdkkkkdgGb...",
    "...bGGgddddgGGb...",
    "...bGGggddggGGb...",
    "....bGGgddgGGb....",
    "....bGGddddGGb....",
    ".....bGyyyyGb.....",
    ".....bGGddGGb.....",
    "......bGddGb......",
    ".......bGGb.......",
    "........bb........",
]

# Heavy-brow variant: thicker brow band, single-pixel deep-set eyes.
HEAVY = TOP[:6] + [
    "bGwGddkkkkkkddgGwGb"[:18],
    "bGGddkkkkkkkkddgGGb"[:18],
    "bGgdkkkRxxRkkkdgGGb"[:18],
    "bGgdkkkRxxRkkkdgGGb"[:18],
    "bGGddkkkkkkkkddgGGb"[:18],
] + TOP[11:]

VARIANTS = {
    "A · baseline": ("the current one", TOP + LOWER_BASE),
    "B · wide jaw": ("broader lower face / jaw", TOP + LOWER_WIDE),
    "C · gaunt": ("narrower, more skeletal", NARROW),
    "D · big grin": ("prominent toothy grin", TOP + LOWER_GRIN),
    "E · heavy brow": ("deeper brow, smaller eyes", HEAVY + LOWER_BASE),
}


def validate() -> None:
    bad = []
    for label, (_, rows) in VARIANTS.items():
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            offenders = [(i, len(r)) for i, r in enumerate(rows) if len(r) != len(rows[0])]
            bad.append((label, sorted(widths), offenders))
    if bad:
        for label, widths, offenders in bad:
            print(f"BAD {label}: widths={widths} offenders={offenders}")
        raise SystemExit("Fix non-rectangular variants above.")
    print("All variants rectangular:", {k: f"{len(v[1][0])}x{len(v[1])}" for k, v in VARIANTS.items()})


def emit() -> None:
    import json
    data = {label: {"desc": desc, "rows": rows} for label, (desc, rows) in VARIANTS.items()}
    html = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>T-800 skull ~ proof sheet</title>
<style>
  body{margin:0;background:radial-gradient(ellipse at 50% -10%,#2a1310,#0a0706 55%) fixed;color:#d9cfc9;font-family:-apple-system,Segoe UI,Roboto,sans-serif}
  body::after{content:"";position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(0,0,0,0) 0 2px,rgba(0,0,0,.22) 2px 3px);mix-blend-mode:multiply}
  .wrap{max-width:1000px;margin:0 auto;padding:2rem 1rem 4rem}
  h1{color:#ff5141;text-shadow:0 0 10px rgba(255,45,32,.4);letter-spacing:.04em}
  p.sub{color:#9a8c84}
  .sheet{display:flex;flex-wrap:wrap;gap:1.4rem;justify-content:center}
  .card{background:#0c0807;border:1px solid #8e1810;border-radius:8px;padding:1rem 1.2rem 1.2rem;text-align:center;box-shadow:0 0 24px rgba(255,45,32,.08)}
  .label{font-family:ui-monospace,Menlo,monospace;color:#ffb000;font-weight:600;letter-spacing:.06em}
  .desc{color:#9a8c84;font-size:.8rem;margin:.1rem 0 .8rem}
  .grid{display:grid;gap:0;width:max-content;margin:0 auto;filter:drop-shadow(0 0 6px rgba(255,45,32,.2))}
  .px{width:10px;height:10px}
  .px.eye{box-shadow:0 0 5px 1px #ff5141,0 0 11px 3px rgba(255,45,32,.55);position:relative;z-index:2}
</style></head><body><div class="wrap">
<h1>&#129302; T-800 ~ proof sheet</h1>
<p class="sub">Five variations of the pixel skull. Pick one (A&ndash;E) and I&rsquo;ll promote it into the explainer header and the TUI.</p>
<div class="sheet" id="sheet"></div>
</div>
<script>
const PAL=__PAL__;
const VARIANTS=__DATA__;
const sheet=document.getElementById('sheet');
for(const [label,info] of Object.entries(VARIANTS)){
  const card=document.createElement('div'); card.className='card';
  const lab=document.createElement('div'); lab.className='label'; lab.textContent=label; card.appendChild(lab);
  const desc=document.createElement('div'); desc.className='desc'; desc.textContent=info.desc; card.appendChild(desc);
  const grid=document.createElement('div'); grid.className='grid';
  const W=info.rows[0].length;
  grid.style.gridTemplateColumns='repeat('+W+',10px)';
  for(const row of info.rows){ for(const ch of row){ const d=document.createElement('div'); d.className='px'; const c=PAL[ch]; if(c){ d.style.background=c; if(ch==='R'||ch==='x') d.classList.add('eye'); } grid.appendChild(d);} }
  card.appendChild(grid); sheet.appendChild(card);
}
</script></body></html>"""
    html = html.replace("__PAL__", json.dumps(PAL)).replace("__DATA__", json.dumps(data))
    out = Path(__file__).resolve().parent / "skull-proofs.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    validate()
    emit()
