#!/usr/bin/env python3
"""Build a local sales KPI snapshot for CyberTender Radar."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "docs" / "data" / "opportunities.json"
OUTREACH_PATH = ROOT / "business" / "outreach_tracker.csv"
LEADS_PATH = ROOT / "business" / "lead_pipeline.csv"
FOLLOWUP_PATH = ROOT / "business" / "followup_draft_queue.csv"
OUTREACH_DRAFT_PATH = ROOT / "business" / "outreach_draft_queue.csv"
SNAPSHOT_PATH = ROOT / "business" / "kpi_snapshot.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def status_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter((row.get("status") or "unknown").strip() or "unknown" for row in rows)


def load_feed() -> dict:
    if not FEED_PATH.exists():
        return {}
    return json.loads(FEED_PATH.read_text(encoding="utf-8"))


def write_snapshot() -> None:
    feed = load_feed()
    outreach_rows = read_csv(OUTREACH_PATH)
    lead_rows = read_csv(LEADS_PATH)
    followup_rows = read_csv(FOLLOWUP_PATH)
    draft_rows = read_csv(OUTREACH_DRAFT_PATH)

    outreach_counts = status_counts(outreach_rows)
    lead_counts = status_counts(lead_rows)
    generated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    lines = [
        "# CyberTender Radar KPI Snapshot",
        "",
        f"Generated: {generated}",
        "",
        "## Revenue",
        "",
        "- Paid customers tracked locally: 0",
        "- Monthly recurring revenue tracked locally: GBP 0",
        "- Target monthly recurring revenue: GBP 10,000",
        "",
        "## Product",
        "",
        f"- Current feed opportunities: {feed.get('summary', {}).get('total', 0)}",
        f"- High-confidence opportunities: {feed.get('summary', {}).get('highConfidence', 0)}",
        f"- Largest opportunity value: {feed.get('summary', {}).get('largestValueLabel', 'Value not disclosed')}",
        "",
        "## Outreach",
        "",
    ]

    if outreach_counts:
        for status, count in sorted(outreach_counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No first-batch outreach rows.")

    lines.extend(["", "## Lead Pipeline", ""])
    if lead_counts:
        for status, count in sorted(lead_counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No lead-pipeline rows.")

    lines.extend(
        [
            "",
            "## Draft Queues",
            "",
            f"- New outreach drafts queued locally: {len(draft_rows)}",
            f"- Follow-up drafts due locally: {len(followup_rows)}",
            "",
            "## Current Constraint",
            "",
            "- Confirm Gumroad payouts are active before scaling beyond manual outreach.",
            "",
        ]
    )
    SNAPSHOT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    write_snapshot()
    print(f"Wrote {SNAPSHOT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
