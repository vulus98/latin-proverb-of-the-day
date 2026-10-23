"""Notify the local WhatsApp test recipient about new private feedback."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TARGET = "+381638991909"
OPENCLAW = "/home/vbozic/.local/bin/openclaw"
GATEWAY = "openclaw-gateway.service"
STATE = Path.home() / ".local" / "state" / "latin-proverb-of-the-day" / "feedback.json"


def request_supabase(method: str, path: str, body: dict | None = None) -> tuple[dict, dict]:
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/" + path
    headers = {
        "apikey": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": "Bearer " + os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    request = urllib.request.Request(
        url,
        headers=headers,
        data=json.dumps(body).encode() if body else None,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        rows = json.load(response)
    return (rows[0] if rows else {}, rows[1] if len(rows) > 1 else {})


def send_message(message: str) -> None:
    started = subprocess.run(
        ["systemctl", "--user", "is-active", "--quiet", GATEWAY],
        check=False,
    ).returncode != 0
    if started:
        subprocess.run(["systemctl", "--user", "start", GATEWAY], check=True)
    try:
        for _ in range(30):
            status = subprocess.run([OPENCLAW, "gateway", "status"], capture_output=True, text=True)
            if "Connectivity probe: ok" in status.stdout + status.stderr:
                break
            time.sleep(1)
        else:
            raise RuntimeError("OpenClaw gateway did not become ready")
        subprocess.run(
            [OPENCLAW, "message", "send", "--channel", "whatsapp", "--target", TARGET,
             "--message", message, "--json"],
            check=True,
        )
    finally:
        if started:
            subprocess.run(["systemctl", "--user", "stop", GATEWAY], check=False)


def main() -> None:
    marker = json.loads(STATE.read_text()) if STATE.exists() else {}
    query = "feedback?notified_at=is.null&order=created_at.asc&limit=1"
    row, _ = request_supabase("GET", query)
    if not row or row.get("id") == marker.get("id"):
        return
    choice = {
        "delightful": "Jana thinks the proverb is surprisingly delightful.",
        "wise": "Jana thinks the proverb is wisely curated.",
        "thoughtful": "Jana says the proverb makes her think.",
        "cute": "Jana thinks the page is cute and clever.",
        "honest": "Jana doesn't like today's proverb.",
    }.get(row["choice"], "Jana left feedback on today's proverb.")
    send_message(f"✨ You guys have something to discuss: {choice}\n"
                 f"Proverb: {row['proverb_latin']}")
    request_supabase(
        "PATCH",
        f"feedback?id=eq.{urllib.parse.quote(row['id'])}",
        {"notified_at": datetime.now(timezone.utc).isoformat()},
    )
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"id": row["id"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
