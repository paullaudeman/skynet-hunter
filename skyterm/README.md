# skyterm ~ an amber-phosphor terminal theme

The Skynet Hunter CRT look, for your everyday terminal. Monochrome amber phosphor on
a glowing dark-amber ground, drawn from the same palette as the [web HUD](../web/index.html).
Two functional accents are kept (phosphor-green for added/success, burnt-red for
errors/diffs) so it stays usable for real work.

Pick the path that fits how you want to live in it:

| Terminal | What you get | Daily-driver? |
|---|---|---|
| **iTerm2** | the amber colour scheme (no scanlines ~ iTerm2 has no shaders) | yes ~ lightweight, zero strain |
| **Ghostty** | amber colours + an optional GLSL CRT shader, dialed subtle | yes ~ GPU-fast, the smart middle |
| **cool-retro-term** | the *full* CRT ~ amber, scanlines, glow, curvature, flicker | the vibe terminal, not all-day |

## Palette

```
bg #160d03   fg #ffb43c   cursor #ffb43c   green #7df06a   red #c0531c
dim #c0801f  faint #5c3c10  pale #e6cfa0  selection #3a2a12
```

The colour files are generated from `build.py` (run `python3 skyterm/build.py` to
regenerate after a palette change).

## iTerm2

1. iTerm2 → Settings → Profiles → Colors → Color Presets… → **Import…**
2. Choose `skyterm.itermcolors`.
3. Color Presets… → select **skyterm**.

A glowing amber phosphor scheme, daily-usable. For the chunky CRT font feel, pair it
with a pixel font (e.g. **VT323**, used in the web HUD) or any crisp mono you like.

## Ghostty

Append `ghostty/skyterm` to `~/.config/ghostty/config`, or drop it in
`~/.config/ghostty/themes/skyterm` and set `theme = skyterm`. Reload with
`Cmd+Shift+,`. For the CRT layer, point `custom-shader` at a retro GLSL shader and
keep it subtle ~ the comment block in the file shows where.

## cool-retro-term ~ the full CRT

```
brew install --cask cool-retro-term
```

Then Settings, and dial it to the skyterm look (cool-retro-term's profile JSON schema
drifts between versions, so these are the knobs rather than an import file):

- **Profile:** start from **Amber** (or Default Amber).
- **Font colour:** `#ffb43c`  ·  **Background:** `#160d03`
- **Effects:** Scanlines **on**, Bloom ~`0.55`, Screen curvature ~`0.15`, Burn-in low,
  Static noise ~`0.08`, Flickering low, Jitter low, Ambient light low.

Gorgeous, but heavier ~ scanlines on small text all day cause eye strain and tax the
GPU. Best as the *mood* terminal (demos, late-night hacking), with iTerm2 or Ghostty
for real work.

## Starship

Back up your `~/.config/starship.toml`, then copy `starship.toml` over it for an
amber prompt that matches. It recolours the prompt modules; merge the `[..]` blocks
into your existing config if you'd rather keep your format.

---

*Part of [Skynet Hunter](../README.md). Could graduate to its own repo ~ a tiny,
installable amber-CRT terminal identity.*
