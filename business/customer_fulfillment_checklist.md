# Customer Fulfillment Checklist

Run this when a new Gumroad subscriber appears.

## First 10 Minutes

1. Send `business/customer_welcome_email.md`.
2. Confirm the subscriber can open the live feed, daily brief, CSV, and RSS.
3. Ask for their target services, regions, and buyer watchlist.
4. Record the subscriber in the private customer tracker.

## First 24 Hours

1. Review their requested keywords against `scripts/fetch_opportunities.py`.
2. Add useful terms to the keyword lists or false-positive list.
3. Regenerate the feed with `python scripts/fetch_opportunities.py`.
4. Check whether their requested profile produces useful matches.
5. Reply with the best 3 current opportunities.

## Weekly

1. Send a short note with the best matches from that week.
2. Ask whether any false positives should be excluded.
3. Record whether the customer opened, replied, shortlisted, or cancelled.

## Cancellation Save

If a customer cancels, ask one question:

`What was missing from the feed that would have made this worth keeping?`

Use the answer to improve keywords, positioning, or pricing.
