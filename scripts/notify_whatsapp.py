"""Send the latest published proverb through the local OpenClaw WhatsApp gateway."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

REPOSITORY_DATA = (
    "https://raw.githubusercontent.com/vulus98/latin-proverb-of-the-day/main/"
    "data/today.json"
)
TARGET = "+381638991909"
STATE = Path.home() / ".local" / "state" / "latin-proverb-of-the-day" / "whatsapp.json"
OPENCLAW = "/home/vbozic/.local/bin/openclaw"
GATEWAY = "openclaw-gateway.service"
SITE = "https://vulus98.github.io/latin-proverb-of-the-day/"


def fetch_today() -> dict[str, str]:
    request = urllib.request.Request(REPOSITORY_DATA, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=30) as response:
        entry = json.load(response)
    required = ("date", "latin", "meaning")
    if any(not isinstance(entry.get(field), str) or not entry[field].strip() for field in required):
        raise RuntimeError("Published proverb data is incomplete")
    return entry


def gateway_is_active() -> bool:
    return subprocess.run(
        ["systemctl", "--user", "is-active", "--quiet", GATEWAY],
        check=False,
    ).returncode == 0


def send_message(message: str) -> None:
    started_gateway = not gateway_is_active()
    if started_gateway:
        subprocess.run(["systemctl", "--user", "start", GATEWAY], check=True)
    try:
        for _ in range(30):
            status = subprocess.run(
                [OPENCLAW, "gateway", "status"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "Connectivity probe: ok" in status.stdout + status.stderr:
                break
            time.sleep(1)
        else:
            raise RuntimeError("OpenClaw gateway did not become ready")
        subprocess.run(
            [
                OPENCLAW,
                "message",
                "send",
                "--channel",
                "whatsapp",
                "--target",
                TARGET,
                "--message",
                message,
                "--presentation",
                json.dumps({
                    "text": message,
                    "buttons": [{
                        "label": "Read today's proverb",
                        "url": SITE,
                    }],
                }),
                "--json",
            ],
            check=True,
        )
    finally:
        if started_gateway:
            subprocess.run(["systemctl", "--user", "stop", GATEWAY], check=False)


def main() -> None:
    entry = fetch_today()
    marker = f"{entry['date']}:{entry['latin']}"
    previous = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    if previous.get("sent") == marker:
        return
    send_message("A new Latin proverb is out.")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"sent": marker}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
