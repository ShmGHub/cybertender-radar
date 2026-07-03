#!/usr/bin/env python3
"""Build local follow-up drafts for sent outreach rows that are due."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER_PATH = ROOT / "business" / "outreach_tracker.csv"
CSV_PATH = ROOT / "business" / "followup_draft_queue.csv"
MD_PATH = ROOT / "business" / "followup_draft_queue.md"
BUSINESS_EMAIL = "cybertenderbusiness@gmail.com"
CHECKOUT_URL = "https://cybertender.gumroad.com/l/msidq"
LIVE_FEED_URL = "https://shmghub.github.io/cybertender-radar/"


def today() -> date:
    return date.today()


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def load_tracker() -> list[dict[str, str]]:
    with TRACKER_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def is_due(row: dict[str, str], run_date: date) -> bool:
    if row.get("status") != "sent":
        return False
    follow_up = parse_date(row.get("next_follow_up", ""))
    return follow_up is not None and follow_up <= run_date


def body(row: dict[str, str]) -> str:
    company = row.get("company") or "there"
    niche = row.get("niche") or "cyber and IT"
    return "\n".join(
        [
            f"Hi {company} team,",
            "",
            "Quick follow-up. CyberTender Radar is built for teams that do not want to check procurement portals every morning.",
            "",
            f"It filters official sources for {niche} opportunities and links back to the original notices so your team can verify fit quickly.",
            "",
            f"Live feed: {LIVE_FEED_URL}",
            f"Scout feed: {CHECKOUT_URL}",
            "",
            "Worth trying for your bid pipeline?",
            "",
            "Thanks,",
            "CyberTender Radar",
            "",
            "If this is not relevant, reply \"no\" and there will be no further follow-up.",
        ]
    )


def build_rows(rows: list[dict[str, str]], run_date: date) -> list[dict[str, str]]:
    drafts = []
    for row in rows:
        if not is_due(row, run_date):
            continue
        drafts.append(
            {
                "from": BUSINESS_EMAIL,
                "to": row.get("email_or_profile", ""),
                "company": row.get("company", ""),
                "subject": "Re: public-sector cyber tenders",
                "body": body(row),
                "status": "followup_due",
                "next_follow_up": row.get("next_follow_up", ""),
            }
        )
    return drafts


def write_csv(rows: list[dict[str, str]]) -> None:
    fields = ["from", "to", "company", "subject", "body", "status", "next_follow_up"]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]], run_date: date) -> None:
    lines = [
        "# Follow-Up Draft Queue",
        "",
        f"Generated for: {run_date.isoformat()}",
        f"Sender account required: `{BUSINESS_EMAIL}`",
        "",
        "Do not send these to recipients who have replied, bounced, unsubscribed, or said no.",
        "",
    ]
    if not rows:
        lines.extend(["No follow-up drafts are due today.", ""])
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
    run_date = today()
    rows = build_rows(load_tracker(), run_date)
    write_csv(rows)
    write_markdown(rows, run_date)
    print(f"Wrote {len(rows)} follow-up drafts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
