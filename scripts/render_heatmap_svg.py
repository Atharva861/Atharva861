#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded, colored boxes, with a diagonal
line-after-line slide-down reveal (plays once on load, then freezes).

Usage:
  python scripts/render_heatmap_svg.py
Output:
  contrib-heatmap.svg
"""
import json
import datetime

INPUT = "data/contributions.json"
OUTPUT = "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end, beyond GitHub's own level 4)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
PAD_LEFT = 34
PAD_TOP = 26
PAD_BOTTOM = 34
PAD_RIGHT = 16

BG = "#0d1117"
TEXT_COLOR = "#8b949e"
TITLE_COLOR = "#c9d1d9"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Monday=0 .. Sunday=6

STAGGER = 0.006   # per-cell delay multiplier (diagonal wipe)
CELL_DUR = 0.35


def level_for_count(count, max_count):
    if count == 0:
        return 0
    if max_count <= 0:
        return 1
    # bucket into 5 non-zero levels
    frac = count / max_count
    if frac > 0.8:
        return 5
    if frac > 0.6:
        return 4
    if frac > 0.4:
        return 3
    if frac > 0.15:
        return 2
    return 1


def build_weeks(days):
    """Group days into weeks (columns), Sunday-first, matching GitHub's layout."""
    by_date = {d["date"]: d for d in days}
    if not by_date:
        return []

    all_dates = sorted(by_date.keys())
    start = datetime.date.fromisoformat(all_dates[0])
    end = datetime.date.fromisoformat(all_dates[-1])

    # rewind start to the preceding Sunday so weeks align in 7-day columns
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        iso = cur.isoformat()
        entry = by_date.get(iso, {"date": iso, "count": 0, "level": 0})
        week.append(entry)
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += datetime.timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks


def escape_xml(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def build_svg(data):
    days = data["days"]
    stats = data["stats"]
    username = data.get("username", "")

    weeks = build_weeks(days)
    n_weeks = len(weeks)
    max_count = max((d["count"] for d in days if d), default=0)

    grid_w = n_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = PAD_LEFT + grid_w + PAD_RIGHT
    height = PAD_TOP + grid_h + PAD_BOTTOM

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')
    parts.append(
        f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;'
        f'font-size:11px;fill:{TEXT_COLOR};}}</style>'
    )

    # day-of-week labels
    for dow, label in DOW_LABELS.items():
        y = PAD_TOP + dow * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="2" y="{y}">{label}</text>')

    # month labels — placed above the first week column that starts a new month
    last_month = None
    for wi, week in enumerate(weeks):
        first_valid = next((d for d in week if d), None)
        if not first_valid:
            continue
        date = datetime.date.fromisoformat(first_valid["date"])
        if date.month != last_month:
            x = PAD_LEFT + wi * (CELL + GAP)
            parts.append(f'<text x="{x}" y="{PAD_TOP - 10}">{MONTH_LABELS[date.month - 1]}</text>')
            last_month = date.month

    # cells, diagonal-staggered reveal (delay based on column + row)
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            x = PAD_LEFT + wi * (CELL + GAP)
            y = PAD_TOP + di * (CELL + GAP)
            level = level_for_count(day["count"], max_count)
            color = PALETTE[level]
            delay = (wi + di) * STAGGER
            title = escape_xml(f'{day["count"]} contributions on {day["date"]}')

            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{color}" opacity="0" transform="translate(0,-6)">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.3f}s" dur="{CELL_DUR}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -6" to="0 0" begin="{delay:.3f}s" dur="{CELL_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
                f'</rect>'
            )

    # legend (Less -> More)
    legend_y = height - PAD_BOTTOM + 14
    legend_x = PAD_LEFT
    parts.append(f'<text x="{legend_x}" y="{legend_y + 9}">Less</text>')
    lx = legend_x + 32
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 9}">More</text>')

    # stats footer (right-aligned)
    total = stats.get("total_contributions", 0)
    footer = f'{total:,} contributions in the last year'
    parts.append(
        f'<text x="{width - PAD_RIGHT}" y="{legend_y + 9}" text-anchor="end" '
        f'fill="{TITLE_COLOR}">{escape_xml(footer)}</text>'
    )

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    with open(INPUT) as f:
        data = json.load(f)

    svg = build_svg(data)
    with open(OUTPUT, "w") as f:
        f.write(svg)
    print(f"Done -> {OUTPUT}")


if __name__ == "__main__":
    main()
