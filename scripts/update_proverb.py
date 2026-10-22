"""Generate and publish one new Latin proverb with Gemini."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TODAY = ROOT / "data" / "today.json"
SEEN = ROOT / "data" / "seen.json"
MODEL = "gemini-2.5-flash"
FIELDS = ("latin", "translation", "meaning", "anecdote", "prompt")


def request_proverb(seen_latin: list[str]) -> dict[str, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    prompt = f"""Return exactly one JSON object with these string fields:
latin, translation, meaning, anecdote, prompt.

Choose a genuine Latin proverb that is not in this already-used list:
{json.dumps(seen_latin, ensure_ascii=False)}

The anecdote must describe the proverb's origin or historical use. Do not
invent a quotation, author, date, or story. If the origin is uncertain, say so
clearly. The prompt must be a concise, philosophical question connected to the
proverb, introduced on the page as "Question to ponder". Do not include
Markdown, commentary, or extra keys."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.8,
        },
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:"
        f"generateContent?key={urllib.parse.quote(api_key)}"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Gemini request failed: {error}") from error
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        proverb = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("Gemini returned an invalid JSON response") from error
    if set(proverb) != set(FIELDS) or not all(
        isinstance(proverb[field], str) and proverb[field].strip() for field in FIELDS
    ):
        raise RuntimeError("Gemini response did not contain the required fields")
    if proverb["latin"].strip().casefold() in {item.casefold() for item in seen_latin}:
        raise RuntimeError("Gemini returned a previously used proverb")
    return proverb


def main() -> None:
    now = datetime.now(ZoneInfo("Europe/Belgrade"))
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else []
    today = now.date().isoformat()
    previous = next((entry for entry in seen if entry["date"] == today), None)
    if previous:
        raise RuntimeError("Today's proverb is already recorded; no update needed")

    proverb = request_proverb([entry["latin"] for entry in seen])
    seen.append({"date": today, "latin": proverb["latin"]})
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = {
        "date": now.strftime("%A, %d %B %Y"),
        **proverb,
    }
    TODAY.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
