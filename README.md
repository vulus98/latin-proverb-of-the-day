# Latin Proverb of the Day

A small shared page for learning Latin proverbs together. It publishes one
proverb every day at 09:00 in the `Europe/Belgrade` timezone.

The GitHub Actions workflow runs hourly because GitHub schedules use UTC and
cannot express daylight-saving time. It only commits a new proverb during the
09:00 local hour, then deploys the page to GitHub Pages.

To add more proverbs, edit [`data/proverbs.json`](data/proverbs.json). The
selection is deterministic, so rerunning the workflow does not skip ahead.
