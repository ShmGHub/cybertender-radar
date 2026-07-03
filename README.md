# CyberTender Radar

CyberTender Radar is a zero-upfront-cost tender-alert business for small
cybersecurity, MSP, and IT services suppliers. It pulls official public
opportunities, scores them for niche fit, and publishes a static dashboard that
can run from GitHub Pages.

## What It Does

- Searches UK Contracts Finder and Grants.gov for cyber and IT opportunities.
- Scores each result for relevance, urgency, value, and SME fit.
- Publishes a live feed, CSV export, and daily brief.
- Includes optional SAM.gov support through a `SAM_API_KEY` secret.
- Runs on free GitHub Actions with no Python package dependencies.
- Checks the live site and checkout daily with a production health workflow.
- Publishes an RSS feed and sample brief for outreach and prospect review.

Live site: <https://shmghub.github.io/cybertender-radar/>

Subscribe: <https://cybertender.gumroad.com/l/msidq>

## Run Locally

```powershell
python scripts/fetch_opportunities.py
python -m http.server 8000 -d docs
```

Then open `http://localhost:8000`.

## Free Hosting

1. Push this repository to GitHub.
2. In repository settings, enable GitHub Pages from the `docs` folder.
3. The workflow in `.github/workflows/daily-radar.yml` refreshes the feed every
   weekday at 06:17 UTC.

## Revenue Path

- Scout: `GBP 49/month`, daily ranked feed and CSV.
- Bid Team: `GBP 99/month`, feed plus shortlist notes and deadline watchlist.
- Pipeline: `GBP 199/month`, custom keywords and buyer watchlist.

Break-even target for `GBP 10k/month`:

- 205 Scout customers, or
- 102 Bid Team customers, or
- 51 Pipeline customers.

## Manual Setup Still Needed

No code can legally create your bank, payment processor, or seller accounts for
you. The current dashboard CTA points to the Gumroad checkout for CyberTender
Radar Scout. Update the subscription link in `docs/index.html` if the checkout
URL changes.

## Guardrails

The product is a discovery layer. Every card links back to official source
material, and subscribers should verify the original notice before bidding.

## Launch Assets

- Customer onboarding: `business/customer_welcome_email.md`
- Outreach sequence: `business/outreach_sequence.md`
- First outreach batch: `business/first_outreach_batch.md`
- Next outreach batch: `business/next_outreach_batch.md`
- Second batch Gmail drafts: `business/second_batch_gmail_drafts.md`
- Daily sales checklist: `business/daily_sales_checklist.md`
- Payment admin checklist: `business/payment_admin_checklist.md`
- Operations runbook: `business/operations_runbook.md`
- Outreach tracker: `business/outreach_tracker.csv`
- Lead pipeline: `business/lead_pipeline.csv`
- Outreach draft queue: `business/outreach_draft_queue.md`
- Follow-up draft queue: `business/followup_draft_queue.md`
- Daily sales packet: `business/daily_sales_packet.md`
