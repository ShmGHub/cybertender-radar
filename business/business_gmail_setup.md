# Business Gmail Setup

Use `cybertenderbusiness@gmail.com` for all outbound CyberTender Radar email.
Do not send outreach from the personal Gmail account.

## Required Before Sending

1. Connect Gmail in Codex as `cybertenderbusiness@gmail.com`.
2. Confirm the Gmail profile shown by Codex is `cybertenderbusiness@gmail.com`.
3. Confirm the sender display name is `CyberTender Radar`.
4. Recreate the outreach draft queue in that inbox.
5. Send messages one by one, only to public company contact addresses.

## Current Blocker

Resolved: the Codex Gmail connector is now authenticated as
`cybertenderbusiness@gmail.com`, and the first 10 outreach emails were sent from
that inbox on 2026-07-03.

## After Connection

Ask Codex to:

1. Check the connected Gmail profile.
2. Watch for replies.
3. Record replies in `business/outreach_tracker.csv`.
4. Send the 2026-07-06 follow-up only to recipients who have not replied.
