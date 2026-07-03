#!/usr/bin/env python3
"""Build local outreach draft copy for the business Gmail account."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "docs" / "data" / "opportunities.json"
TRACKER_PATH = ROOT / "business" / "outreach_tracker.csv"
CSV_PATH = ROOT / "business" / "outreach_draft_queue.csv"
MD_PATH = ROOT / "business" / "outreach_draft_queue.md"

SITE_URL = "https://shmghub.github.io/cybertender-radar/"
SAMPLE_URL = "https://shmghub.github.io/cybertender-radar/sample-brief.html"
CHECKOUT_URL = "https://cybertender.gumroad.com/l/msidq"
BUSINESS_EMAIL = "cybertenderbusiness@gmail.com"


def load_feed() -> dict[str, Any]:
    return json.loads(FEED_PATH.read_text(encoding="utf-8"))


def load_tracker() -> list[dict[str, str]]:
    with TRACKER_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def opportunity_lookup(feed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup = {}
    for item in feed.get("opportunities", []):
        title = str(item.get("title") or "")
        if title:
            lookup[title.lower()] = item
    return lookup


def subject(row: dict[str, str]) -> str:
    niche = (row.get("niche") or "").lower()
    if "forensic" in niche:
        return "Digital forensics public-sector tender feed"
    return f"Public-sector cyber tenders for {row.get('company')}"


def body(row: dict[str, str], opportunity: dict[str, Any] | None) -> str:
    company = row.get("company") or "there"
    niche = row.get("niche") or "cyber and IT"
    opp_title = row.get("opportunity_mentioned") or "a relevant public-sector opportunity"
    buyer = (opportunity or {}).get("buyer") or "the public sector"
    value = (opportunity or {}).get("valueLabel") or "a material contract value"
    deadline = (opportunity or {}).get("deadlineDate") or "a published tender deadline"

    return "\n".join(
        [
            f"Hi {company} team,",
            "",
            "CyberTender Radar is a daily shortlist of public-sector cyber, IT, and digital forensics tenders for suppliers.",
            "",
            f"Today it flagged {opp_title} from {buyer}. It is listed at {value}, with a deadline of {deadline}.",
            f"That looks relevant to {niche} teams that want more public-sector bid opportunities.",
            "",
            f"Live preview: {SITE_URL}",
            f"Sample brief: {SAMPLE_URL}",
            f"Scout feed: {CHECKOUT_URL}",
            "",
            "Worth trying for your bid pipeline?",
            "",
            "Thanks,",
            "CyberTender Radar",
            "",
            "If this is not relevant, reply \"no\" and there will be no follow-up.",
        ]
    )


def build_rows(feed: dict[str, Any], tracker_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    lookup = opportunity_lookup(feed)
    drafts = []
    for row in tracker_rows:
        if row.get("status") not in {"business_gmail_needed", "business_gmail_draft_ready", "draft_ready"}:
            continue
        opportunity = lookup.get((row.get("opportunity_mentioned") or "").lower())
        drafts.append(
            {
                "from": BUSINESS_EMAIL,
                "to": row.get("email_or_profile", ""),
                "company": row.get("company", ""),
                "subject": subject(row),
                "body": body(row, opportunity),
                "source_url": row.get("source_url", ""),
                "status": row.get("status", ""),
            }
        )
    return drafts


def write_csv(rows: list[dict[str, str]]) -> None:
    fields = ["from", "to", "company", "subject", "body", "source_url", "status"]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Outreach Draft Queue",
        "",
        f"Sender account required: `{BUSINESS_EMAIL}`",
        "",
        "Do not send these from any personal Gmail account.",
        "",
    ]
    if not rows:
        lines.extend(
            [
                "No active draft rows. The current first batch is marked sent in",
                "`business/outreach_tracker.csv`.",
                "",
            ]
        )
    for index, row in enumerate(rows, 1):
        lines.extend(
            [
                f"## {index}. {row['company']}",
                "",
                f"To: {row['to']}",
                f"Subject: {row['subject']}",
                "",
                "```text",
                row["body"],
                "```",
                "",
            ]
        )
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    feed = load_feed()
    rows = build_rows(feed, load_tracker())
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} outreach drafts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
