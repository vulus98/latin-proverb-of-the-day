"""Publish the proverb selected for the current Europe/Belgrade date."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PROVERBS = ROOT / "data" / "proverbs.json"
TODAY = ROOT / "data" / "today.json"
SEEN = ROOT / "data" / "seen.json"


def main() -> None:
    now = datetime.now(ZoneInfo("Europe/Belgrade"))
    proverbs = json.loads(PROVERBS.read_text(encoding="utf-8"))
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else []
    today = now.date().isoformat()
    previous = next((entry for entry in seen if entry["date"] == today), None)
    if previous:
        proverb = next(item for item in proverbs if item["latin"] == previous["latin"])
    else:
        used = {entry["latin"] for entry in seen}
        proverb = next((item for item in proverbs if item["latin"] not in used), None)
        if proverb is None:
            raise RuntimeError("All proverbs have been used; add more before publishing another.")
        seen.append({"date": today, "latin": proverb["latin"]})
        SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = {
        "date": now.strftime("%A, %d %B %Y"),
        "latin": proverb["latin"],
        "translation": proverb["translation"],
        "meaning": proverb["meaning"],
        "anecdote": proverb["anecdote"],
        "prompt": proverb["prompt"],
    }
    TODAY.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
