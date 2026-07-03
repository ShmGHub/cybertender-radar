# Operations Runbook

## Daily Automation

GitHub Actions refreshes the opportunity feed every weekday at 06:17 UTC.
The site health check runs every weekday at 07:41 UTC.

Workflow:

- `.github/workflows/daily-radar.yml`
- `.github/workflows/site-health.yml`
- Runs `python scripts/fetch_opportunities.py`
- Writes `docs/data/opportunities.json`
- Writes `docs/data/opportunities.csv`
- Writes `docs/data/latest_brief.md`
- Commits changed feed files back to `main`

## Live URLs

- Site: https://shmghub.github.io/cybertender-radar/
- Gumroad: https://cybertender.gumroad.com/l/msidq
- Brief: https://shmghub.github.io/cybertender-radar/data/latest_brief.md
- CSV: https://shmghub.github.io/cybertender-radar/data/opportunities.csv

## Morning Check

1. Confirm the live site loads.
2. Confirm the generated timestamp changed after the scheduled run.
3. Confirm the site health workflow passed.
4. Check that at least one opportunity is present.
5. Send 10-30 targeted outreach messages using `business/outreach_sequence.md`.

## Customer Delivery

When someone subscribes through Gumroad:

1. Send `business/customer_welcome_email.md`.
2. Ask which service areas they care about.
3. Add useful keyword requests to `scripts/fetch_opportunities.py`.

## Gumroad Settings

Recommended product settings:

- Product name: CyberTender Radar Scout
- Price: GBP 49/month
- Button/checkout link: https://cybertender.gumroad.com/l/msidq
- Post-purchase redirect: https://shmghub.github.io/cybertender-radar/thanks.html
- Product content: paste the live site, brief, and CSV links.

## Weekly Review

Every Friday:

1. Review false positives in the feed.
2. Add or downweight keywords in `scripts/fetch_opportunities.py`.
3. Count outreach sent, replies, trials, and paid subscribers.
4. Adjust the target customer niche if replies are weak.
