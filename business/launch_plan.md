# CyberTender Radar Launch Plan

## Positioning

Daily cyber and IT procurement intelligence for small suppliers that do not have
a dedicated bid-research team.

## First Customer Profile

- UK or US cybersecurity consultancy, MSP, cloud security firm, or IT support
  provider.
- 5 to 50 staff.
- Already wants public-sector work but does not check portals daily.
- Can justify `GBP 49-199/month` if one saved opportunity creates a bid.

## Offer

Public preview:

- Latest 20-80 ranked opportunities.
- Official source links.
- CSV export.

Paid subscription:

- Daily email brief.
- Full CSV export.
- Watchlist for buyer, region, keyword, deadline, and framework alerts.
- Monthly market map of recurring buyers and high-value frameworks.

## Acquisition

Start with direct outbound because it costs nothing and reaches buyers fastest.

1. Search LinkedIn and Google Maps for "cybersecurity consultancy", "MSP", and
   "IT support" in one region.
2. Send a short note with one live opportunity from the feed.
3. Offer a free 7-day sample brief.
4. Convert to the Scout plan.

Example message:

```text
Subject: 3 public-sector cyber opportunities this week

Hi,

I run CyberTender Radar, a daily shortlist of public-sector cyber and IT tenders
for small suppliers.

This week it found [specific opportunity] from [buyer], with a deadline on
[date]. I can send you a free 7-day sample for your exact services.

Worth receiving the sample?
```

## Automation Roadmap

- Phase 1: Static public feed and CSV, already included.
- Phase 2: Add payment link and paid export page.
- Phase 3: Add subscriber list through a free email tool or Gumroad posts.
- Phase 4: Add custom profiles by duplicating the keyword arrays in
  `scripts/fetch_opportunities.py`.
- Phase 5: Add SAM.gov when an API key is available.

## Risk Controls

- Never imply a customer is guaranteed to win a contract.
- Always link to official source notices.
- Keep a visible generated timestamp.
- Score and label confidence instead of hiding uncertainty.
- Do not scrape private portals or bypass login walls.
