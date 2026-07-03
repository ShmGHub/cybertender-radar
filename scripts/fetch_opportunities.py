#!/usr/bin/env python3
"""Build the CyberTender Radar public opportunity feed.

The script intentionally uses only the Python standard library so the business
can run on free GitHub Actions without dependency installation or paid services.
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = ROOT / "docs" / "data"
PRIVATE_DATA_DIR = ROOT / "data"

CONTRACTS_FINDER_SEARCH_URL = (
    "https://www.contractsfinder.service.gov.uk/api/rest/2/search_notices/json"
)
CONTRACTS_FINDER_DETAIL_URL = (
    "https://www.contractsfinder.service.gov.uk/api/rest/2/get_published_notice/json/{id}"
)
GRANTS_GOV_SEARCH_URL = "https://api.grants.gov/v1/api/search2"
SAM_GOV_SEARCH_URL = "https://api.sam.gov/prod/opportunities/v2/search"

PRODUCT_PROFILE = {
    "name": "CyberTender Radar",
    "niche": "Cybersecurity and IT services opportunities for small suppliers",
    "positioning": (
        "Daily ranked public-sector cyber, security, and IT opportunities with "
        "SME-friendly filters."
    ),
    "targetCustomer": "Small cybersecurity consultancies, MSPs, and IT services firms",
}

CONTRACT_KEYWORDS = [
    "cyber security",
    "cybersecurity",
    "information security",
    "penetration testing",
    "security operations",
    "incident response",
    "cloud security",
    "network security",
    "IT support",
    "digital security",
    "ISO 27001",
]

GRANT_KEYWORDS = [
    "cybersecurity",
    "cyber security",
    "information security",
    "cyberinfrastructure",
    "AI readiness",
]

TERM_WEIGHTS = {
    "cyber": 8,
    "cybersecurity": 18,
    "cyber security": 18,
    "digital forensics": 16,
    "information security": 14,
    "penetration testing": 15,
    "vulnerability": 12,
    "incident response": 12,
    "security operations": 11,
    "managed detection": 11,
    "soc": 10,
    "siem": 10,
    "cloud security": 10,
    "zero trust": 10,
    "network security": 9,
    "iso 27001": 8,
    "data protection": 7,
    "gdpr": 6,
    "it services": 6,
    "it support": 6,
    "managed service": 5,
    "helpdesk": 5,
    "digital": 2,
    "software": 2,
}

FALSE_POSITIVE_TERMS = {
    "cctv": 16,
    "guarding": 18,
    "door entry": 14,
    "fire alarm": 14,
    "physical security": 18,
    "security cameras": 14,
    "surveillance": 12,
    "manned guarding": 20,
    "social enterprise": 12,
    "design print": 16,
    "printing": 12,
    "tree equity": 20,
    "urban resilience": 12,
    "marketing": 10,
    "recruitment": 10,
}

CORE_TERMS = {
    "cyber",
    "cybersecurity",
    "cyber security",
    "digital forensics",
    "information security",
    "penetration testing",
    "vulnerability",
    "incident response",
    "security operations",
    "managed detection",
    "soc",
    "siem",
    "cloud security",
    "zero trust",
    "network security",
    "iso 27001",
    "data protection",
    "gdpr",
}

MANAGED_IT_TERMS = {
    "it support",
    "managed service",
    "helpdesk",
}


@dataclass
class SourceRun:
    name: str
    status: str = "ok"
    fetched: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "fetched": self.fetched,
            "errors": self.errors,
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def request_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    payload = None
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "CyberTenderRadar/0.1 (+https://github.com)",
    }
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    request = Request(url, data=payload, method=method, headers=request_headers)
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = text.replace("\u00c2\u00a3", "\u00a3")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(value: Any) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None

    for candidate in (text, text.replace("Z", "+00:00")):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.date().isoformat()


def days_until(value: datetime | None, now: datetime) -> int | None:
    if value is None:
        return None
    return (value.date() - now.date()).days


def money_label(value: float | int | None, currency: str) -> str:
    if not value:
        return "Value not disclosed"
    amount = float(value)
    symbol = "\u00a3" if currency == "GBP" else "$" if currency == "USD" else f"{currency} "
    if amount >= 1_000_000:
        return f"{symbol}{amount / 1_000_000:.1f}m"
    if amount >= 1_000:
        return f"{symbol}{amount / 1_000:.0f}k"
    return f"{symbol}{amount:,.0f}"


def source_text(opportunity: dict[str, Any]) -> str:
    fields = [
        opportunity.get("title", ""),
        opportunity.get("description", ""),
        opportunity.get("buyer", ""),
        opportunity.get("category", ""),
        " ".join(opportunity.get("tags", [])),
    ]
    return clean_text(" ".join(fields)).lower()


def contains_term(text: str, term: str) -> bool:
    if term == "cyber":
        return re.search(r"(?<![a-z0-9])cyber[a-z0-9-]*", text, flags=re.IGNORECASE) is not None
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def matched_terms(text: str) -> list[str]:
    matches = []
    for term in TERM_WEIGHTS:
        if contains_term(text, term):
            matches.append(term)
    return matches


def score_opportunity(opportunity: dict[str, Any], now: datetime) -> dict[str, Any]:
    primary_text = clean_text(
        " ".join(
            [
                opportunity.get("title", ""),
                opportunity.get("description", ""),
                opportunity.get("buyer", ""),
            ]
        )
    ).lower()
    category_text = clean_text(opportunity.get("category", "")).lower()
    text = f"{primary_text} {category_text}"
    score = 18

    if opportunity.get("source") == "UK Contracts Finder":
        score += 12
    elif opportunity.get("source") == "Grants.gov":
        score += 6
    elif opportunity.get("source") == "SAM.gov":
        score += 10

    primary_terms = matched_terms(primary_text)
    category_terms = [term for term in matched_terms(category_text) if term not in primary_terms]
    terms = primary_terms + category_terms[:4]
    score += sum(TERM_WEIGHTS[term] for term in primary_terms)
    score += sum(max(1, TERM_WEIGHTS[term] // 3) for term in category_terms[:4])

    for term, penalty in FALSE_POSITIVE_TERMS.items():
        if contains_term(text, term):
            score -= penalty

    value = opportunity.get("value")
    if isinstance(value, (int, float)):
        if value >= 1_000_000:
            score += 15
        elif value >= 100_000:
            score += 9
        elif value >= 25_000:
            score += 5

    deadline_days = opportunity.get("deadlineInDays")
    if deadline_days is None:
        score += 2
    elif deadline_days < 0:
        score -= 40
    elif deadline_days <= 7:
        score -= 10
    elif 8 <= deadline_days <= 45:
        score += 12
    elif 46 <= deadline_days <= 120:
        score += 7
    elif deadline_days > 365:
        score -= 4

    if opportunity.get("isSmeSuitable"):
        score += 10

    if any(contains_term(text, word) for word in ("framework", "dynamic purchasing", "dps")):
        score += 8

    if contains_term(text, "small business"):
        score += 8

    has_strong_primary_match = any(
        term in CORE_TERMS or term in MANAGED_IT_TERMS for term in primary_terms
    )
    has_only_broad_category_match = not primary_terms and bool(category_terms)
    if not has_strong_primary_match:
        score -= 25
    if has_only_broad_category_match:
        score -= 10

    score = max(0, min(100, score))
    opportunity["matchScore"] = score
    opportunity["matchedTerms"] = terms[:8]
    opportunity["confidence"] = "High" if score >= 70 else "Medium" if score >= 45 else "Low"
    opportunity["whyItMatters"] = explain_match(opportunity, now)
    opportunity["nextStep"] = next_step(opportunity)
    opportunity["tags"] = build_tags(opportunity, text)
    return opportunity


def explain_match(opportunity: dict[str, Any], now: datetime) -> str:
    parts: list[str] = []
    if opportunity.get("matchedTerms"):
        parts.append("Matches " + ", ".join(opportunity["matchedTerms"][:3]))
    if opportunity.get("isSmeSuitable"):
        parts.append("marked SME-suitable")
    if opportunity.get("value"):
        parts.append(f"value around {opportunity.get('valueLabel')}")
    deadline_days = opportunity.get("deadlineInDays")
    if isinstance(deadline_days, int) and deadline_days >= 0:
        parts.append(f"deadline in {deadline_days} days")
    if not parts:
        parts.append("Relevant source text matched the cyber/IT profile")
    return "; ".join(parts) + "."


def next_step(opportunity: dict[str, Any]) -> str:
    if opportunity.get("source") == "Grants.gov":
        return "Review eligibility and application package on Grants.gov."
    if opportunity.get("documents"):
        return "Open the official notice and review the linked tender documents."
    return "Open the official notice and confirm fit before bidding."


def build_tags(opportunity: dict[str, Any], text: str) -> list[str]:
    tags = []
    checks = [
        ("Cyber", ("cyber", "information security", "incident response")),
        ("Compliance", ("iso 27001", "gdpr", "audit", "data protection")),
        ("Cloud", ("cloud", "saas", "hosting")),
        ("Network", ("network", "infrastructure", "connectivity")),
        ("Managed IT", ("it support", "managed service", "helpdesk")),
        ("Grant", ("grant", "cooperative agreement")),
        ("Framework", ("framework", "dynamic purchasing", "dps")),
        ("SME-friendly", ("small business", "sme")),
    ]
    for label, needles in checks:
        if any(needle in text for needle in needles):
            tags.append(label)
    if opportunity.get("isSmeSuitable") and "SME-friendly" not in tags:
        tags.append("SME-friendly")
    return tags[:6]


def normalize_contracts_finder_item(item: dict[str, Any], keyword: str, now: datetime) -> dict[str, Any]:
    published = parse_date(item.get("publishedDate"))
    deadline = parse_date(item.get("deadlineDate"))
    value = item.get("valueLow") or item.get("valueHigh") or None
    notice_id = clean_text(item.get("id"))
    opportunity = {
        "id": f"contracts-finder:{notice_id}",
        "source": "UK Contracts Finder",
        "market": "UK",
        "sourceKeyword": keyword,
        "title": clean_text(item.get("title")),
        "buyer": clean_text(item.get("organisationName")),
        "status": clean_text(item.get("noticeStatus")),
        "opportunityType": clean_text(item.get("noticeType")) or "Contract",
        "category": clean_text(item.get("cpvDescriptionExpanded") or item.get("cpvDescription")),
        "description": clean_text(item.get("description")),
        "publishedDate": iso_or_none(published),
        "deadlineDate": iso_or_none(deadline),
        "deadlineInDays": days_until(deadline, now),
        "value": value,
        "valueCurrency": "GBP",
        "valueLabel": money_label(value, "GBP"),
        "region": clean_text(item.get("regionText") or item.get("region")),
        "url": f"https://www.contractsfinder.service.gov.uk/notice/{notice_id}",
        "apiUrl": CONTRACTS_FINDER_DETAIL_URL.format(id=notice_id),
        "isSmeSuitable": bool(item.get("isSuitableForSme")),
        "documents": [],
    }
    return opportunity


def normalize_grants_gov_item(item: dict[str, Any], keyword: str, now: datetime) -> dict[str, Any]:
    published = parse_date(item.get("openDate"))
    deadline = parse_date(item.get("closeDate"))
    grant_id = clean_text(item.get("id"))
    opportunity = {
        "id": f"grants-gov:{grant_id}",
        "source": "Grants.gov",
        "market": "US",
        "sourceKeyword": keyword,
        "title": clean_text(item.get("title")),
        "buyer": clean_text(item.get("agency") or item.get("agencyName") or item.get("agencyCode")),
        "status": clean_text(item.get("oppStatus")),
        "opportunityType": clean_text(item.get("docType")) or "Grant",
        "category": "Grant opportunity",
        "description": clean_text(
            " ".join(
                [
                    clean_text(item.get("title")),
                    clean_text(item.get("number")),
                    clean_text(item.get("agency") or item.get("agencyName")),
                ]
            )
        ),
        "publishedDate": iso_or_none(published),
        "deadlineDate": iso_or_none(deadline),
        "deadlineInDays": days_until(deadline, now),
        "value": None,
        "valueCurrency": "USD",
        "valueLabel": "Grant value varies",
        "region": "United States",
        "url": f"https://www.grants.gov/search-results-detail/{grant_id}",
        "apiUrl": GRANTS_GOV_SEARCH_URL,
        "isSmeSuitable": "small business" in clean_text(item).lower(),
        "documents": [],
        "referenceNumber": clean_text(item.get("number")),
    }
    return opportunity


def fetch_contracts_finder(now: datetime) -> tuple[list[dict[str, Any]], SourceRun]:
    run = SourceRun(name="UK Contracts Finder")
    results: list[dict[str, Any]] = []
    for keyword in CONTRACT_KEYWORDS:
        body = {
            "searchCriteria": {
                "types": ["Contract", "Pipeline", "PreProcurement"],
                "statuses": ["Open"],
                "keyword": keyword,
                "suitableForSme": True,
            },
            "size": 40,
        }
        try:
            data = request_json(CONTRACTS_FINDER_SEARCH_URL, method="POST", body=body)
            notices = data.get("noticeList", [])
            run.fetched += len(notices)
            for hit in notices:
                item = hit.get("item") or {}
                if item:
                    results.append(normalize_contracts_finder_item(item, keyword, now))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            run.errors.append(f"{keyword}: {exc}")
    if run.errors and not results:
        run.status = "error"
    elif run.errors:
        run.status = "partial"
    return results, run


def fetch_grants_gov(now: datetime) -> tuple[list[dict[str, Any]], SourceRun]:
    run = SourceRun(name="Grants.gov")
    results: list[dict[str, Any]] = []
    for keyword in GRANT_KEYWORDS:
        body = {
            "rows": 40,
            "keyword": keyword,
            "oppStatuses": "posted|forecasted",
        }
        try:
            data = request_json(GRANTS_GOV_SEARCH_URL, method="POST", body=body)
            hits = ((data.get("data") or {}).get("oppHits")) or []
            run.fetched += len(hits)
            for item in hits:
                results.append(normalize_grants_gov_item(item, keyword, now))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            run.errors.append(f"{keyword}: {exc}")
    if run.errors and not results:
        run.status = "error"
    elif run.errors:
        run.status = "partial"
    return results, run


def fetch_sam_gov(now: datetime) -> tuple[list[dict[str, Any]], SourceRun]:
    """Optional future source. Runs only when SAM_API_KEY is available."""
    run = SourceRun(name="SAM.gov", status="skipped")
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        run.errors.append("Set SAM_API_KEY to include US federal contract opportunities.")
        return [], run

    results: list[dict[str, Any]] = []
    params = {
        "api_key": api_key,
        "title": "cybersecurity",
        "active": "true",
        "limit": "50",
        "postedFrom": now.strftime("%m/%d/%Y"),
        "postedTo": now.strftime("%m/%d/%Y"),
    }
    query = "&".join(f"{key}={value}" for key, value in params.items())
    try:
        data = request_json(f"{SAM_GOV_SEARCH_URL}?{query}")
        # The SAM.gov payload shape changes by endpoint version. Preserve the raw
        # count for observability until this optional integration is configured.
        items = data.get("opportunitiesData") or data.get("data") or []
        run.fetched = len(items) if isinstance(items, list) else 0
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        run.status = "error"
        run.errors.append(str(exc))
    return results, run


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        key = item["id"]
        if key not in seen:
            seen[key] = item
            continue
        existing = seen[key]
        existing_terms = set(existing.get("sourceKeywords", [existing.get("sourceKeyword", "")]))
        existing_terms.add(item.get("sourceKeyword", ""))
        existing["sourceKeywords"] = sorted(term for term in existing_terms if term)
    return list(seen.values())


def enrich_contracts_finder(opportunities: list[dict[str, Any]], limit: int = 40) -> None:
    enriched = 0
    for opportunity in opportunities:
        if enriched >= limit:
            return
        if opportunity.get("source") != "UK Contracts Finder":
            continue
        notice_id = opportunity["id"].split(":", 1)[1]
        try:
            detail = request_json(CONTRACTS_FINDER_DETAIL_URL.format(id=notice_id), timeout=20)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            continue

        details = detail.get("additionalDetails") or []
        links = []
        attachments = []
        for row in details:
            data_type = clean_text(row.get("dataType")).lower()
            if data_type == "link" and row.get("link"):
                links.append(clean_text(row.get("link")))
            elif data_type == "attachment" and row.get("filename"):
                attachments.append(clean_text(row.get("filename")))
        if links:
            opportunity["sourceLinks"] = links[:5]
        if attachments:
            opportunity["documents"] = attachments[:8]
        enriched += 1


def build_feed() -> dict[str, Any]:
    now = utc_now()
    all_items: list[dict[str, Any]] = []
    source_runs: list[SourceRun] = []

    for fetcher in (fetch_contracts_finder, fetch_grants_gov, fetch_sam_gov):
        items, run = fetcher(now)
        all_items.extend(items)
        source_runs.append(run)

    opportunities = dedupe(all_items)
    for item in opportunities:
        score_opportunity(item, now)

    opportunities = [
        item
        for item in opportunities
        if item.get("confidence") in {"High", "Medium"}
        and item.get("matchScore", 0) >= 42
        and item.get("matchedTerms")
    ]
    opportunities.sort(
        key=lambda item: (
            item.get("matchScore", 0),
            -(item.get("deadlineInDays") or 9999),
        ),
        reverse=True,
    )
    opportunities = opportunities[:80]
    enrich_contracts_finder(opportunities)

    high = sum(1 for item in opportunities if item.get("confidence") == "High")
    values = [item["value"] for item in opportunities if isinstance(item.get("value"), (int, float))]
    summary = {
        "total": len(opportunities),
        "highConfidence": high,
        "markets": sorted({item.get("market") for item in opportunities if item.get("market")}),
        "sources": sorted({item.get("source") for item in opportunities if item.get("source")}),
        "largestValue": max(values) if values else None,
        "largestValueLabel": money_label(max(values), "GBP") if values else "Value not disclosed",
        "nextDeadlineDays": min(
            [
                item["deadlineInDays"]
                for item in opportunities
                if isinstance(item.get("deadlineInDays"), int) and item["deadlineInDays"] >= 0
            ],
            default=None,
        ),
    }

    return {
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "profile": PRODUCT_PROFILE,
        "summary": summary,
        "sources": [run.as_dict() for run in source_runs],
        "opportunities": opportunities,
    }


def write_json(feed: dict[str, Any]) -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in (PUBLIC_DATA_DIR / "opportunities.json", PRIVATE_DATA_DIR / "opportunities.json"):
        path.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(feed: dict[str, Any]) -> None:
    path = PUBLIC_DATA_DIR / "opportunities.csv"
    fields = [
        "matchScore",
        "confidence",
        "source",
        "market",
        "title",
        "buyer",
        "valueLabel",
        "deadlineDate",
        "deadlineInDays",
        "url",
        "whyItMatters",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in feed["opportunities"]:
            writer.writerow({field: item.get(field, "") for field in fields})


def write_brief(feed: dict[str, Any]) -> None:
    path = PUBLIC_DATA_DIR / "latest_brief.md"
    lines = [
        f"# {PRODUCT_PROFILE['name']} Daily Brief",
        "",
        f"Generated: {feed['generatedAt']}",
        "",
        f"Tracked opportunities: {feed['summary']['total']}",
        f"High-confidence matches: {feed['summary']['highConfidence']}",
        "",
        "## Top Matches",
        "",
    ]
    for index, item in enumerate(feed["opportunities"][:10], 1):
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- Score: {item['matchScore']} ({item['confidence']})",
                f"- Buyer: {item.get('buyer') or 'Unknown'}",
                f"- Value: {item.get('valueLabel')}",
                f"- Deadline: {item.get('deadlineDate') or 'Not specified'}",
                f"- Why: {item.get('whyItMatters')}",
                f"- Official link: {item.get('url')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    feed = build_feed()
    write_json(feed)
    write_csv(feed)
    write_brief(feed)
    print(
        f"Wrote {feed['summary']['total']} opportunities "
        f"({feed['summary']['highConfidence']} high-confidence)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
