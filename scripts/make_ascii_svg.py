#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into a monochrome, self-typing
ASCII-art SVG.

Each pixel's brightness is mapped to a character from a density ramp
(bright -> sparse, dark -> dense). Each row is wrapped in a clip-path that
wipes left-to-right, staggered top-to-bottom, so the portrait "prints" once
on load and then freezes (no looping).

Usage:
  python scripts/make_ascii_svg.py
Output:
  avi-ascii.svg  (renamed per-user below)
"""
from PIL import Image

INPUT = "source-prepped.png"
OUTPUT = "ascii-portrait.svg"

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

COLS = 100
CHAR_W = 8.6
CHAR_H = 15
FONT_SIZE = 15
FILL_COLOR = "#c9d1d9"       # light gray, monochrome
BG_COLOR = "#0d1117"          # GitHub-dark-style background
ROW_STAGGER = 0.028           # seconds between each row starting
WIPE_DURATION = 0.5           # seconds for a row's wipe animation


def compute_rows(path, cols):
    """Pick a row count that preserves the source image's aspect ratio,
    accounting for character cells being taller than they are wide."""
    img = Image.open(path)
    src_w, src_h = img.size
    rows = round(cols * (src_h / src_w) * (CHAR_W / CHAR_H))
    return max(1, rows)


def image_to_ascii_grid(path, cols, rows):
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows), Image.LANCZOS)
    pixels = list(img.getdata())
    grid = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]  # 0=black .. 255=white
            # invert: white(255) -> ramp[0] (space), black(0) -> ramp[-1] (dense)
            idx = int((255 - brightness) / 255 * (len(RAMP) - 1))
            row_chars.append(RAMP[idx])
        grid.append("".join(row_chars))
    return grid


def escape_xml(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def build_svg(grid):
    rows_n = len(grid)
    width = COLS * CHAR_W
    height = rows_n * CHAR_H

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>')
    parts.append(
        f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;'
        f'font-size:{FONT_SIZE}px;fill:{FILL_COLOR};white-space:pre;}}</style>'
    )

    for r, row in enumerate(grid):
        row_escaped = escape_xml(row)
        y = (r + 1) * CHAR_H - 3
        clip_id = f"clip{r}"
        row_width = COLS * CHAR_W
        delay = r * ROW_STAGGER

        # clipPath rect animates its width from 0 -> full row width
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{r * CHAR_H:.1f}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{delay:.3f}s" dur="{WIPE_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f'</rect>'
        )
        parts.append('</clipPath>')

        parts.append(f'<g clip-path="url(#{clip_id})">')
        # Each character gets its own textLength-constrained span so glyph
        # width never depends on the renderer's font metrics (avoids drift
        #/compression across different SVG renderers).
        parts.append(
            f'<text x="0" y="{y:.1f}" textLength="{row_width:.1f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{row_escaped}</text>'
        )
        parts.append('</g>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    print(f"Reading {INPUT} ...")
    rows = compute_rows(INPUT, COLS)
    grid = image_to_ascii_grid(INPUT, COLS, rows)
    print(f"Building {COLS}x{rows} SVG ...")
    svg = build_svg(grid)
    with open(OUTPUT, "w") as f:
        f.write(svg)
    print(f"Done -> {OUTPUT}")


if __name__ == "__main__":
    main()
