"""Dev.to cross-post — reads schedule.json, posts due articles to Dev.to.

Run manually or via GitHub Actions cron at 07:00 UTC.

Usage:
    python3 devto_crosspost.py              # Post due articles
    python3 devto_crosspost.py --dry-run    # Preview without posting
    python3 devto_crosspost.py --status     # Show schedule status
"""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from _schedule_utils import (
    load_schedule,
    save_schedule,
    setup_logging,
    validate_article_path,
)
from publish import (
    PublishResult,
    _load_env,
    convert_to_devto,
    find_devto_article_by_title,
    parse_article,
    publish_to_devto,
    update_on_devto,
)

SCRIPT_DIR = Path(__file__).parent
LOG_PATH = SCRIPT_DIR / "devto_crosspost.log"

logger = logging.getLogger(__name__)


def _needs_posting(value: str | None) -> bool:
    return value is None or value == "" or value == "pending"


def _is_post_entry(entry: dict[str, Any]) -> bool:
    """All entries in posts/ are eligible for Dev.to cross-posting."""
    return entry.get("file", "").startswith("posts/")


def _is_done(entry: dict[str, Any]) -> bool:
    return not _needs_posting(entry.get("devto"))


def show_status(schedule: dict[str, Any]) -> None:
    today = date.today()
    logger.info("Today: %s", today)
    logger.info("%-12s %-45s %-10s %s", "Date", "File", "Dev.to", "Status")
    logger.info("-" * 80)
    for entry in schedule["articles"]:
        d = entry["date"]
        f = entry["file"]
        devto = "done" if _is_done(entry) else "-"
        entry_date = date.fromisoformat(d)
        if _is_done(entry):
            status = "posted"
        elif entry_date <= today:
            status = "DUE"
        else:
            status = "scheduled"
        logger.info("%-12s %-45s %-10s %s", d, f, devto, status)


def _try_publish(
    publish_fn: Callable[[], PublishResult], *, dry_run: bool, title: str,
) -> tuple[str | None, bool]:
    if dry_run:
        logger.info("  [DRY-RUN] Would publish to Dev.to: %s", title)
        return None, False
    result = publish_fn()
    if result.success:
        logger.info("  Dev.to OK: %s", result.url)
        return result.url, False
    logger.warning("  Dev.to FAIL: %.200s", result.error)
    return None, True


def _load_devto_key() -> str | None:
    _load_env(SCRIPT_DIR / ".env")
    devto_key = os.environ.get("DEVTO_API_KEY")
    if not devto_key:
        logger.error("Missing env var: DEVTO_API_KEY")
        return None
    return devto_key


def _process_entry(
    entry: dict[str, Any], devto_key: str, *, dry_run: bool,
) -> tuple[dict[str, Any], int]:
    article_path = validate_article_path(entry["file"])
    if article_path is None:
        return entry, 1

    article = parse_article(article_path)
    logger.info("Processing: %s (date=%s)", article.title, entry["date"])

    devto_tags = entry.get("devto_tags")
    cover_image = entry.get("cover_image")

    def _devto_upsert() -> PublishResult:
        payload = convert_to_devto(
            article,
            devto_tags_override=devto_tags,
            cover_image_url=cover_image,
        )
        existing_id = find_devto_article_by_title(article.title, devto_key)
        if existing_id:
            logger.info("  Dev.to: existing article found (%s), updating", existing_id)
            return update_on_devto(existing_id, payload, devto_key)
        return publish_to_devto(payload, devto_key)

    url, failed = _try_publish(
        _devto_upsert, dry_run=dry_run, title=article.title,
    )
    if url:
        return {**entry, "devto": url}, 0
    return entry, 1 if failed else 0


def publish_due(schedule: dict[str, Any], *, dry_run: bool = False) -> int:
    devto_key = _load_devto_key()
    if devto_key is None:
        return 1

    today = date.today()
    posted_count = 0
    errors = 0
    updated_articles: list[dict[str, Any]] = []
    remaining = list(schedule["articles"])

    for i, entry in enumerate(remaining):
        if not _is_post_entry(entry):
            updated_articles.append(entry)
            continue
        if _is_done(entry):
            updated_articles.append(entry)
            continue
        entry_date = date.fromisoformat(entry["date"])
        if entry_date > today:
            updated_articles.append(entry)
            continue

        updated_entry, entry_errors = _process_entry(entry, devto_key, dry_run=dry_run)
        updated_articles.append(updated_entry)
        errors += entry_errors
        posted_count += 1

        if updated_entry is not entry and not dry_run:
            all_articles = updated_articles + remaining[i + 1:]
            save_schedule({**schedule, "articles": all_articles})

    if posted_count == 0:
        logger.info("Nothing due today.")
    elif not dry_run:
        save_schedule({**schedule, "articles": updated_articles})
        logger.info(
            "Schedule updated. %d article(s) processed, %d error(s).",
            posted_count, errors,
        )
    else:
        logger.info("[DRY-RUN] %d article(s) would be posted.", posted_count)

    return 1 if errors > 0 else 0


def main() -> int:
    setup_logging(logger, LOG_PATH)
    parser = argparse.ArgumentParser(description="Dev.to cross-post")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument("--status", action="store_true", help="Show schedule status")
    args = parser.parse_args()

    schedule = load_schedule()

    if args.status:
        show_status(schedule)
        return 0

    return publish_due(schedule, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
