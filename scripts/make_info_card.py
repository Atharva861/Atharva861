#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style info card SVG.

Renders a title bar plus colored key/value rows, each fading + sliding in
on a short stagger so it looks like it's printing next to the ASCII
portrait. Set STATIC=1 to emit a frozen frame (all rows already visible) —
useful for local previews / Quick Look, since it never animates twice.

Usage:
  python scripts/make_info_card.py
Output:
  info-card.svg
"""
import os

OUTPUT = "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH = 600
ROW_H = 34
PAD_X = 24
PAD_TOP = 54
TITLEBAR_H = 40

BG = "#0d1117"
PANEL_BG = "#161b22"
BORDER = "#30363d"
TITLE_COLOR = "#c9d1d9"
KEY_COLOR = "#58a6ff"     # blue, like neofetch labels
VAL_COLOR = "#c9d1d9"
ACCENT = "#39d353"        # green accent, matches heatmap top color
DOT_RED = "#ff5f56"
DOT_YELLOW = "#ffbd2e"
DOT_GREEN = "#27c93f"

TITLE = "atharva@github ~ $ neofetch"

# key/value rows — edit freely
ROWS = [
    ("Name", "Atharva Salunke"),
    ("Role", "Frontend / Full-Stack Developer"),
    ("Now", "Open to full-time roles - immediate joining"),
    ("Prev", "Contract dev for 2 NZ clients (Jan-Jul 2026)"),
    ("Stack", "React - Next.js - TypeScript - Tailwind CSS"),
    ("Also", "Python - PyTorch - OpenCV - Scikit-learn"),
    ("Research", "IEEE-accepted paper: Hindi handwritten text OCR"),
    ("Education", "B.E. Computer Engineering, 2022-2026"),
    ("Highlights", "93% OCR accuracy - 2 production client sites"),
    ("Contact", "github.com/Atharva861"),
]

ROW_STAGGER = 0.12
FADE_DUR = 0.45


def escape_xml(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def build_svg():
    height = PAD_TOP + ROW_H * len(ROWS) + 26

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}">'
    )
    parts.append(
        f'<style>'
        f'.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;}}'
        f'.title{{font-size:14px;fill:{TITLE_COLOR};}}'
        f'.key{{font-size:14.5px;fill:{KEY_COLOR};font-weight:600;}}'
        f'.val{{font-size:14.5px;fill:{VAL_COLOR};}}'
        f'</style>'
    )

    # panel background + border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="10" '
        f'fill="{PANEL_BG}" stroke="{BORDER}" stroke-width="1"/>'
    )

    # title bar
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{TITLEBAR_H}" rx="10" fill="#1c2128"/>'
    )
    parts.append(f'<rect x="0.5" y="{TITLEBAR_H-9}" width="{WIDTH-1}" height="9" fill="#1c2128"/>')
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{TITLEBAR_H}" rx="10" '
        f'fill="none" stroke="{BORDER}" stroke-width="1"/>'
    )
    # traffic-light dots
    for i, color in enumerate([DOT_RED, DOT_YELLOW, DOT_GREEN]):
        cx = 22 + i * 18
        parts.append(f'<circle cx="{cx}" cy="{TITLEBAR_H/2:.0f}" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH/2:.0f}" y="{TITLEBAR_H/2+5:.0f}" text-anchor="middle" '
        f'class="mono title">{escape_xml(TITLE)}</text>'
    )

    # rows
    for i, (key, val) in enumerate(ROWS):
        y = PAD_TOP + i * ROW_H
        text_y = y + ROW_H * 0.65
        delay = i * ROW_STAGGER

        group_attrs = ""
        anims = ""
        if not STATIC:
            group_attrs = ' opacity="0" transform="translate(-14,0)"'
            anims = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-14 0" to="0 0" begin="{delay:.2f}s" dur="{FADE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            )

        parts.append(f'<g{group_attrs}>')
        if anims:
            parts.append(anims)
        parts.append(
            f'<text x="{PAD_X}" y="{text_y:.1f}" class="mono key">{escape_xml(key)}</text>'
        )
        parts.append(
            f'<text x="{PAD_X + 118}" y="{text_y:.1f}" class="mono val">{escape_xml(val)}</text>'
        )
        parts.append('</g>')

    # bottom accent line (color swatch strip, like neofetch's palette row)
    swatch_y = height - 20
    swatch_colors = [DOT_RED, DOT_YELLOW, DOT_GREEN, "#58a6ff", "#bc8cff", ACCENT]
    for i, c in enumerate(swatch_colors):
        x = PAD_X + i * 20
        parts.append(f'<rect x="{x}" y="{swatch_y}" width="14" height="14" rx="3" fill="{c}"/>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    svg = build_svg()
    with open(OUTPUT, "w") as f:
        f.write(svg)
    mode = "static" if STATIC else "animated"
    print(f"Done ({mode}) -> {OUTPUT}")


if __name__ == "__main__":
    main()
