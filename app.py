import os
import re
import subprocess
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone

from flask import Flask, jsonify, send_from_directory


APP_PORT = int(os.environ.get("PORT", "8080"))
WINDOW_SECONDS = 60 * 60  # last 60 minutes

CATEGORY_MAP = {
    # Streaming
    "youtube.com": "Streaming",
    "netflix.com": "Streaming",
    "twitch.tv": "Streaming",
    "spotify.com": "Streaming",
    "disneyplus.com": "Streaming",
    "primevideo.com": "Streaming",
    # Gaming
    "steamcontent.com": "Gaming",
    "epicgames.com": "Gaming",
    "riotgames.com": "Gaming",
    "battlenet.com": "Gaming",
    "playstation.com": "Gaming",
    # Messaging
    "discord.com": "Messaging",
    "whatsapp.net": "Messaging",
    "slack.com": "Messaging",
    "telegram.org": "Messaging",
    # Social
    "twitter.com": "Social",
    "instagram.com": "Social",
    "tiktok.com": "Social",
    "facebook.com": "Social",
}


def now_ts() -> float:
    return time.time()


def iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def get_primary_interface() -> str:
    env_iface = os.environ.get("INTERFACE")
    if env_iface:
        return env_iface
    try:
        p = subprocess.run(
            ["route", "-n", "get", "default"],
            check=False,
            capture_output=True,
            text=True,
        )
        if p.returncode == 0:
            for line in p.stdout.splitlines():
                if line.strip().startswith("interface:"):
                    return line.split(":", 1)[1].strip() or "en0"
    except Exception:
        pass
    return "en0"


def normalize_domain(domain: str) -> str:
    d = domain.strip().lower().rstrip(".")
    if d.startswith("www."):
        d = d[4:]
    return d


def categorize(domain: str) -> str:
    d = normalize_domain(domain)
    for base, cat in CATEGORY_MAP.items():
        if d == base or d.endswith("." + base):
            return cat
    return "Browsing"


TCPDUMP_DOMAIN_RE = re.compile(
    r"""
    \b
    (?:A\?|AAAA\?|CNAME\?|HTTPS\?|SRV\?|PTR\?|TXT\?|NS\?|MX\?)
    \s+
    (?P<domain>[A-Za-z0-9._-]+)
    \.?
    (?:\s+\(\d+\))?
    (?:\s+.*)?$
""",
    re.VERBOSE,
)


class RollingCounter:
    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self._events: deque[tuple[float, str]] = deque()
        self._lock = threading.Lock()

    def add(self, ts: float, category: str) -> None:
        with self._lock:
            self._events.append((ts, category))
            self._prune_locked(ts)

    def snapshot(self) -> tuple[float, list[tuple[str, int]], int]:
        ts = now_ts()
        with self._lock:
            self._prune_locked(ts)
            counts = Counter(cat for _, cat in self._events)
            total = sum(counts.values())
        items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return ts, items, total

    def _prune_locked(self, ts: float) -> None:
        cutoff = ts - self.window_seconds
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()


rolling = RollingCounter(WINDOW_SECONDS)
tcpdump_status = {"running": False, "last_error": None, "iface": None, "started_at": None}

app = Flask(__name__, static_folder="static", static_url_path="")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/stats")
def api_stats():
    ts, items, total = rolling.snapshot()
    categories = []
    if total:
        # Largest Remainder Method so integer percents sum to 100.
        exact = [(name, queries, (queries / total) * 100.0) for name, queries in items]
        floors = [(name, queries, int(pct)) for name, queries, pct in exact]
        used = sum(p for _, _, p in floors)
        remaining = max(0, 100 - used)

        remainders = sorted(
            [(name, queries, pct - int(pct)) for name, queries, pct in exact],
            key=lambda x: (-x[2], -x[1], x[0]),
        )
        bump = {name: 0 for name, _, _ in remainders}
        for i in range(min(remaining, len(remainders))):
            bump[remainders[i][0]] += 1

        for name, queries, base in floors:
            categories.append({"name": name, "percent": base + bump.get(name, 0), "queries": queries})
    else:
        for name, queries in items:
            categories.append({"name": name, "percent": 0, "queries": queries})
    return jsonify(
        {
            "updated": iso_utc(ts),
            "window": "last_60_minutes",
            "total_queries": total,
            "categories": categories,
            "capture": tcpdump_status,
        }
    )


def _tcpdump_reader():
    iface = get_primary_interface()
    tcpdump_status.update(
        {"running": True, "last_error": None, "iface": iface, "started_at": iso_utc(now_ts())}
    )
    cmd = ["tcpdump", "-i", iface, "-l", "-n", "port", "53"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except Exception as e:
        tcpdump_status.update({"running": False, "last_error": f"Failed to start tcpdump: {e}"})
        return

    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            m = TCPDUMP_DOMAIN_RE.search(line)
            if not m:
                continue
            domain = m.group("domain")
            cat = categorize(domain)
            rolling.add(now_ts(), cat)
    except Exception as e:
        tcpdump_status.update({"last_error": f"Error reading tcpdump output: {e}"})
    finally:
        tcpdump_status.update({"running": False})
        try:
            proc.terminate()
        except Exception:
            pass


def start_capture_thread():
    t = threading.Thread(target=_tcpdump_reader, name="tcpdump-reader", daemon=True)
    t.start()


if __name__ == "__main__":
    start_capture_thread()
    app.run(host="127.0.0.1", port=APP_PORT, debug=False, threaded=True)
