#!/usr/bin/env python3
"""Production health checks for CyberTender Radar."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.getenv("CYBERTENDER_SITE_URL", "http://localhost:8000").rstrip("/")
GUMROAD_URL = "https://cybertender.gumroad.com/l/msidq"


def fetch(url: str, timeout: int = 20) -> tuple[int, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "CyberTenderRadarHealthCheck/0.1",
            "Accept": "text/html,application/json,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    checks = [
        (f"{BASE_URL}/", "CyberTender Radar"),
        (f"{BASE_URL}/privacy.html", "Privacy"),
        (f"{BASE_URL}/terms.html", "Terms and Disclaimer"),
        (f"{BASE_URL}/thanks.html", "Your cyber tender feed is ready"),
        (f"{BASE_URL}/sample-brief.html", "Sample daily brief"),
        (f"{BASE_URL}/feed.xml", "CyberTender Radar"),
        (f"{BASE_URL}/robots.txt", "User-agent:"),
    ]
    errors: list[str] = []

    for url, expected in checks:
        try:
            status, body = fetch(url)
            require(status == 200, f"{url} returned {status}", errors)
            require(expected in body, f"{url} missing expected text: {expected}", errors)
        except (HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{redact_url(url)} failed: {exc}")

    try:
        status, body = fetch(f"{BASE_URL}/data/opportunities.json")
        require(status == 200, "opportunities.json did not return 200", errors)
        feed = json.loads(body)
        require(feed.get("summary", {}).get("total", 0) > 0, "feed has no opportunities", errors)
        require("generatedAt" in feed, "feed missing generatedAt", errors)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        errors.append(f"feed check failed: {exc}")

    try:
        status, body = fetch(GUMROAD_URL)
        require(status == 200, f"Gumroad returned {status}", errors)
        require("CyberTender" in body or "gumroad" in body.lower(), "Gumroad page did not look valid", errors)
    except (HTTPError, URLError, TimeoutError) as exc:
        errors.append(f"Gumroad check failed: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CyberTender Radar production health check passed.")
    return 0


def redact_url(url: str) -> str:
    return url.replace(BASE_URL, "SITE_URL")


if __name__ == "__main__":
    sys.exit(main())
