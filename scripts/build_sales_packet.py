#!/usr/bin/env python3
"""Build the daily CyberTender Radar sales packet from feed and tracker data."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "docs" / "data" / "opportunities.json"
TRACKER_PATH = ROOT / "business" / "outreach_tracker.csv"
LEAD_PIPELINE_PATH = ROOT / "business" / "lead_pipeline.csv"
PACKET_PATH = ROOT / "business" / "daily_sales_packet.md"
FOLLOWUPS_PATH = ROOT / "business" / "outreach_followups_due.csv"

SITE_URL = "https://shmghub.github.io/cybertender-radar/"
SAMPLE_BRIEF_URL = "https://shmghub.github.io/cybertender-radar/sample-brief.html"
CHECKOUT_URL = "https://cybertender.gumroad.com/l/msidq"


def load_feed() -> dict[str, Any]:
    return json.loads(FEED_PATH.read_text(encoding="utf-8"))


def load_tracker() -> list[dict[str, str]]:
    if not TRACKER_PATH.exists():
        return []
    with TRACKER_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_lead_pipeline() -> list[dict[str, str]]:
    if not LEAD_PIPELINE_PATH.exists():
        return []
    with LEAD_PIPELINE_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def money(value: Any) -> str:
    return str(value or "Value not disclosed")


def top_opportunities(feed: dict[str, Any]) -> list[dict[str, Any]]:
    return list(feed.get("opportunities", []))[:5]


def status_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter((row.get("status") or "unknown").strip() or "unknown" for row in rows)


def rows_due(rows: list[dict[str, str]], today: date) -> list[dict[str, str]]:
    due = []
    for row in rows:
        status = (row.get("status") or "").lower()
        follow_up = parse_date(row.get("next_follow_up", ""))
        if not follow_up or follow_up > today:
            continue
        if "draft" in status:
            continue
        if status in {"replied", "converted", "unsubscribed", "not_interested"}:
            continue
        due.append(row)
    return due


def rows_ready_to_send(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status") == "business_gmail_draft_ready"]


def rows_with_followup_drafts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status") == "no_reply_followup_drafted"]


def lead_pipeline_ready(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status") == "business_gmail_draft_ready"]


def next_followup_date(rows: list[dict[str, str]], today: date) -> str:
    dates = []
    for row in rows:
        if row.get("status") != "sent":
            continue
        follow_up = parse_date(row.get("next_follow_up", ""))
        if follow_up and follow_up >= today:
            dates.append(follow_up)
    if not dates:
        return "next scheduled"
    return min(dates).isoformat()


def prospecting_angles(feed: dict[str, Any]) -> list[str]:
    angles = []
    for item in top_opportunities(feed):
        title = item.get("title") or "Untitled opportunity"
        buyer = item.get("buyer") or "Unknown buyer"
        value = money(item.get("valueLabel"))
        deadline = item.get("deadlineDate") or "not specified"
        tags = ", ".join(item.get("tags", [])[:4]) or "cyber/IT"
        angles.append(f"- {title} from {buyer}: {value}, deadline {deadline}. Use for {tags} suppliers.")
    return angles


def write_followups(rows: list[dict[str, str]]) -> None:
    fields = [
        "date",
        "company",
        "email_or_profile",
        "opportunity_mentioned",
        "status",
        "next_follow_up",
        "notes",
    ]
    with FOLLOWUPS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_packet(
    feed: dict[str, Any],
    rows: list[dict[str, str]],
    lead_rows: list[dict[str, str]],
    due: list[dict[str, str]],
) -> None:
    today = date.today()
    counts = status_counts(rows)
    ready = rows_ready_to_send(rows)
    followup_drafts = rows_with_followup_drafts(rows)
    lead_counts = status_counts(lead_rows)
    lead_ready = lead_pipeline_ready(lead_rows)
    next_followup = next_followup_date(rows, today)
    if ready:
        immediate_bottleneck = "review and approve the business Gmail drafts for one-by-one sending."
        next_moves = [
            "1. Review the drafts in cybertenderbusiness@gmail.com.",
            "2. Confirm they should be sent.",
            "3. Send one by one from cybertenderbusiness@gmail.com.",
            "4. Change the tracker status from business_gmail_draft_ready to sent.",
            "5. Watch replies and record them in outreach_tracker.csv.",
        ]
    elif followup_drafts:
        immediate_bottleneck = "review the no-reply follow-up drafts in business Gmail before sending."
        next_moves = [
            "1. Open Gmail drafts in cybertenderbusiness@gmail.com.",
            "2. Review each CyberTender Radar follow-up draft.",
            "3. Send only the drafts that still have no reply, bounce, unsubscribe, or no response.",
            "4. Change sent follow-up rows from no_reply_followup_drafted to followup_sent.",
            "5. Watch replies and record interested, not_interested, bounced, or no-reply outcomes.",
        ]
    elif due:
        immediate_bottleneck = "check replies and prepare due no-reply follow-ups."
        next_moves = [
            "1. Open Gmail label CyberTender Radar/Outreach.",
            "2. Record any replies in outreach_tracker.csv.",
            "3. Remove replied or uninterested prospects from follow-up.",
            "4. Draft concise no-reply follow-ups for the remaining due prospects.",
            "5. Send follow-ups only from cybertenderbusiness@gmail.com.",
        ]
    elif counts.get("sent", 0):
        immediate_bottleneck = f"watch replies and prepare the {next_followup} no-reply follow-up."
        next_moves = [
            "1. Open Gmail label CyberTender Radar/Outreach.",
            "2. Record any replies in outreach_tracker.csv.",
            f"3. Mark no replies for follow-up on {next_followup}.",
            "4. Draft follow-ups only for recipients who have not replied.",
            "5. Keep contact-form leads parked until email-batch signals are clear.",
        ]
    else:
        immediate_bottleneck = "prepare and send the first qualified outreach batch."
        next_moves = [
            "1. Build the first outreach draft queue.",
            "2. Review recipient fit.",
            "3. Send one by one from cybertenderbusiness@gmail.com.",
            "4. Record status in outreach_tracker.csv.",
            "5. Watch replies and follow up only where relevant.",
        ]

    lines = [
        "# CyberTender Radar Daily Sales Packet",
        "",
        f"Generated: {feed.get('generatedAt')}",
        "",
        "## Revenue Target",
        "",
        "- Target: GBP 10,000/month.",
        "- Current paid customers tracked here: 0.",
        "- Practical path: 102 customers at GBP 99/month, or 51 customers at GBP 199/month.",
        f"- Immediate bottleneck: {immediate_bottleneck}",
        "",
        "## Feed Snapshot",
        "",
        f"- Tracked opportunities: {feed.get('summary', {}).get('total', 0)}.",
        f"- High-confidence opportunities: {feed.get('summary', {}).get('highConfidence', 0)}.",
        f"- Largest tracked value: {feed.get('summary', {}).get('largestValueLabel', 'Value not disclosed')}.",
        f"- Live feed: {SITE_URL}",
        f"- Sample brief: {SAMPLE_BRIEF_URL}",
        f"- Checkout: {CHECKOUT_URL}",
        "- Payment admin: confirm Gumroad payouts are active before scaling.",
        "",
        "## Best Hooks Today",
        "",
        *prospecting_angles(feed),
        "",
        "## Outreach State",
        "",
    ]

    if counts:
        for status, count in sorted(counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No outreach rows yet.")

    lines.extend(["", "## Ready In Business Gmail", ""])
    if ready:
        for row in ready:
            lines.append(
                f"- {row.get('company')}: business Gmail draft ready for {row.get('email_or_profile')} using {row.get('opportunity_mentioned')}."
            )
    elif followup_drafts:
        for row in followup_drafts:
            lines.append(
                f"- {row.get('company')}: no-reply follow-up draft ready for {row.get('email_or_profile')}."
            )
    else:
        lines.append("- No business Gmail drafts are marked ready.")

    lines.extend(["", "## Lead Pipeline", ""])
    if lead_counts:
        for status, count in sorted(lead_counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- No lead-pipeline rows yet.")

    if lead_ready:
        lines.extend(["", "## Second Batch Drafts", ""])
        for row in lead_ready:
            lines.append(
                f"- {row.get('company')}: draft ready for {row.get('email_or_profile')} using {row.get('opportunity_hook')}."
            )

    lines.extend(["", "## Follow-Ups Due", ""])
    if due:
        for row in due:
            lines.append(
                f"- {row.get('company')}: follow up on {row.get('opportunity_mentioned')}."
            )
    else:
        lines.append(f"- No follow-ups due on {today.isoformat()}.")

    lines.extend(["", "## Next Manual Move", "", *next_moves, ""])
    PACKET_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    feed = load_feed()
    rows = load_tracker()
    lead_rows = load_lead_pipeline()
    due = rows_due(rows, date.today())
    write_followups(due)
    write_packet(feed, rows, lead_rows, due)
    print(f"Wrote {PACKET_PATH.relative_to(ROOT)} and {FOLLOWUPS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
