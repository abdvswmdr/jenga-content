"""Generate a publication schedule for a batch of articles.

Given an ordered list of article slugs (highest priority first) and a start
date, assigns publication dates and outputs schedule.json entries.

Usage:
    python plan_schedule.py --start 2026-06-01 --slugs "slug1,slug2,slug3"
    python plan_schedule.py --start 2026-06-01 --slugs "slug1,slug2" --cadence mon,wed,fri
    python plan_schedule.py --start 2026-06-01 --input scores.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SCHEDULE_PATH = SCRIPT_DIR / "schedule.json"

DAY_MAP = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}

DEFAULT_CADENCE = [1, 3]  # Tuesday, Thursday


def parse_cadence(cadence_str: str) -> list[int]:
    days = []
    for name in cadence_str.lower().split(","):
        name = name.strip()
        if name not in DAY_MAP:
            print(f"Error: Unknown day '{name}'. Use: {', '.join(DAY_MAP)}", file=sys.stderr)
            raise SystemExit(1)
        days.append(DAY_MAP[name])
    return sorted(days)


def next_publish_date(current: date, publish_days: list[int]) -> date:
    for offset in range(7):
        candidate = current + timedelta(days=offset)
        if candidate.weekday() in publish_days:
            return candidate
    return current


def generate_schedule(
    slugs: list[str],
    start: date,
    publish_days: list[int] | None = None,
    scores: dict[str, dict] | None = None,
) -> list[dict]:
    """Generate schedule entries for a list of article slugs.

    Args:
        slugs: Article slugs in priority order (publish first → last).
        start: Earliest possible publication date.
        publish_days: Weekday numbers (0=Mon, 6=Sun). Default: [1, 3] (Tue/Thu).
        scores: Optional dict mapping slug to score dict for traceability.

    Returns:
        List of schedule entry dicts ready to merge into schedule.json.
    """
    if publish_days is None:
        publish_days = DEFAULT_CADENCE

    entries = []
    current = start

    for slug in slugs:
        publish_date = next_publish_date(current, publish_days)

        entry: dict = {
            "file": f"posts/{slug}.md",
            "date": publish_date.isoformat(),
            "devto": None,
        }

        if scores and slug in scores:
            entry["score"] = scores[slug]

        entries.append(entry)
        current = publish_date + timedelta(days=1)

    return entries


def load_scores(path: Path) -> tuple[list[str], dict[str, dict]]:
    """Load scored articles from JSON file.

    Expected format:
    [
      {"slug": "article-slug", "search": 3, "anchor": 1, "ready": 2, "fresh": 1, "total": 7},
      ...
    ]
    """
    data = json.loads(path.read_text())
    data.sort(key=lambda x: x.get("total", 0), reverse=True)
    slugs = [item["slug"] for item in data]
    scores = {
        item["slug"]: {
            k: item[k] for k in ("search", "anchor", "ready", "fresh", "total")
            if k in item
        }
        for item in data
    }
    return slugs, scores


def merge_into_schedule(new_entries: list[dict]) -> dict:
    if SCHEDULE_PATH.exists():
        schedule = json.loads(SCHEDULE_PATH.read_text())
    else:
        schedule = {"post_time_utc": "07:00", "articles": []}

    existing_files = {e["file"] for e in schedule["articles"]}
    added = 0
    for entry in new_entries:
        if entry["file"] not in existing_files:
            schedule["articles"].append(entry)
            added += 1
        else:
            print(f"  Skip (already exists): {entry['file']}", file=sys.stderr)

    print(f"Added {added} entries to schedule.", file=sys.stderr)
    return schedule


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate publication schedule for article batches",
    )
    parser.add_argument(
        "--start", required=True, type=date.fromisoformat,
        help="Start date (YYYY-MM-DD).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--slugs",
        help="Comma-separated article slugs in priority order.",
    )
    group.add_argument(
        "--input", type=Path,
        help="JSON file with scored articles (auto-sorted by total score).",
    )
    parser.add_argument(
        "--cadence", default="tue,thu",
        help="Comma-separated publish days (default: tue,thu).",
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="Merge into existing schedule.json.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show schedule without writing to file.",
    )

    args = parser.parse_args()
    publish_days = parse_cadence(args.cadence)

    scores: dict[str, dict] | None = None
    if args.input:
        slugs, scores = load_scores(args.input)
    else:
        slugs = [s.strip() for s in args.slugs.split(",")]

    entries = generate_schedule(
        slugs=slugs,
        start=args.start,
        publish_days=publish_days,
        scores=scores,
    )

    print(f"\n{'Date':<14} {'File':<45} {'Score':>5}")
    print("-" * 70)
    for e in entries:
        score_str = str(e["score"]["total"]) if "score" in e else "-"
        print(f"{e['date']:<14} {e['file']:<45} {score_str:>5}")
    print()

    if args.merge and not args.dry_run:
        schedule = merge_into_schedule(entries)
        SCHEDULE_PATH.write_text(
            json.dumps(schedule, indent=2, ensure_ascii=False) + "\n",
        )
        print(f"Written to {SCHEDULE_PATH}", file=sys.stderr)
    elif args.merge and args.dry_run:
        print("[DRY-RUN] Would merge into schedule.json", file=sys.stderr)
    else:
        print(json.dumps(entries, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
