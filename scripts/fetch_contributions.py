#!/usr/bin/env python3
"""
fetch_contributions.py — pull a user's public contribution calendar from
GitHub's public HTML endpoint (no token / GraphQL needed) and derive stats.

GitHub serves this at:
  https://github.com/users/<username>/contributions
It's the same fragment the profile page itself renders.

Usage:
  python scripts/fetch_contributions.py <github-username>
Output:
  data/contributions.json
"""
import sys
import json
import datetime
import requests
from bs4 import BeautifulSoup

OUTPUT = "data/contributions.json"


def fetch_calendar_html(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td> with class "ContributionCalendar-day"
    # and data-date / data-level (newer markup) attributes.
    cells = soup.select("td.ContributionCalendar-day")
    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")
        if date is None:
            continue
        count = 0
        tooltip_id = cell.get("id")
        # Count is usually in an associated <tool-tip> element; fall back
        # to parsing the level if we can't find it.
        days.append({
            "date": date,
            "level": int(level) if level is not None else 0,
            "tooltip_id": tooltip_id,
        })

    # Try to recover actual counts from tool-tip text (e.g. "3 contributions on ...")
    tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.select("tool-tip")}
    for d in days:
        tip = tooltips.get(d["tooltip_id"])
        if tip:
            first_word = tip.split()[0].replace(",", "")
            if first_word.isdigit():
                d["count"] = int(first_word)
            elif first_word.lower() == "no":
                d["count"] = 0
            else:
                d["count"] = 0
        else:
            d["count"] = 0
        del d["tooltip_id"]

    return days


def compute_stats(days):
    days_sorted = sorted(days, key=lambda d: d["date"])
    total = sum(d["count"] for d in days_sorted)

    # current streak (walking back from most recent day)
    current_streak = 0
    for d in reversed(days_sorted):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest = 0
    running = 0
    for d in days_sorted:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    best_day = max(days_sorted, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days_sorted:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": monthly,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_contributions.py <github-username>")
        sys.exit(1)

    username = sys.argv[1]
    print(f"Fetching contribution calendar for {username} ...")
    html = fetch_calendar_html(username)

    print("Parsing days ...")
    days = parse_days(html)
    if not days:
        print("WARNING: no day cells found — GitHub's markup may have changed.")

    print("Computing stats ...")
    stats = compute_stats(days)

    out = {
        "username": username,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Done -> {OUTPUT}")
    print(f"  total: {stats['total_contributions']}, "
          f"current streak: {stats['current_streak']}, "
          f"longest streak: {stats['longest_streak']}")


if __name__ == "__main__":
    main()
