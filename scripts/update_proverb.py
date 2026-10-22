"""Publish the proverb selected for the current Europe/Belgrade date."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PROVERBS = ROOT / "data" / "proverbs.json"
TODAY = ROOT / "data" / "today.json"
EPOCH = datetime(2026, 1, 1, tzinfo=ZoneInfo("Europe/Belgrade"))


def main() -> None:
    now = datetime.now(ZoneInfo("Europe/Belgrade"))
    proverbs = json.loads(PROVERBS.read_text(encoding="utf-8"))
    days_since_epoch = (now.date() - EPOCH.date()).days
    proverb = proverbs[days_since_epoch % len(proverbs)]
    output = {
        "date": now.strftime("%A, %d %B %Y"),
        "latin": proverb["latin"],
        "translation": proverb["translation"],
        "meaning": proverb["meaning"],
        "prompt": proverb["prompt"],
    }
    TODAY.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
