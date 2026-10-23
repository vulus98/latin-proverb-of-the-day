# Latin Proverb of the Day

A small shared page for learning Latin proverbs together. Gemini generates one
new proverb and its supporting content every day at 09:00 in the
`Europe/Belgrade` timezone.

The GitHub Actions workflow runs hourly because GitHub schedules use UTC and
cannot express daylight-saving time. It only commits a new proverb during the
09:00 local hour, then deploys the page to GitHub Pages.

The workflow records each published proverb in
[`data/seen.json`](data/seen.json) and sends that ledger to Gemini, so it asks
for a proverb that has not already been used. The response is validated before
publication. If Gemini is unavailable or returns invalid content, the previous
entry remains published and the workflow reports a warning.

Before enabling generation, add your Google Gemini API key to the repository's
GitHub Actions secrets under the name `GEMINI_API_KEY`. The key must never be
committed to this repository.

WhatsApp reminders use the existing local OpenClaw connection rather than Meta
Cloud API. Install the user units from `systemd/`, then enable
`latin-proverb-whatsapp.timer`. The notifier checks the published GitHub Pages
data every five minutes, sends each proverb only once, and stores its marker in
`~/.local/state/latin-proverb-of-the-day/whatsapp.json`.

The feedback panel is intentionally public and local to the browser: each
choice produces a playful, randomized Roman-council reply. Feedback is not
stored or sent anywhere.
