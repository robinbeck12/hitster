"""Gemeinsame Helfer für add_song.py und check_songs.py."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SONGS_FILE = ROOT / "songs.json"
OEMBED = "https://www.youtube.com/oembed?url={url}&format=json"

_ID = r"[A-Za-z0-9_-]{11}"
_URL_PATTERNS = [
    rf"youtu\.be/({_ID})",
    rf"[?&]v=({_ID})",
    rf"youtube(?:-nocookie)?\.com/(?:embed|shorts|live|v)/({_ID})",
]


def extract_video_id(text: str) -> str | None:
    """Video-ID aus einer YouTube-URL (oder eine nackte 11-stellige ID)."""
    text = text.strip()
    if re.fullmatch(_ID, text):
        return text
    for pattern in _URL_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return None


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def oembed(video_id: str):
    """Fragt YouTube-oEmbed ab. Gibt (status, daten) zurück; status ist eine HTTP-Zahl oder None bei Netzfehler.

    200 = ok und einbettbar, 401/403 = nicht einbettbar, 404 = existiert nicht.
    """
    url = OEMBED.format(url=urllib.parse.quote(watch_url(video_id), safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": "ZeitHit-Tools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, None


def status_text(status) -> str:
    return {
        200: "ok (einbettbar)",
        401: "nicht einbettbar (401)",
        403: "nicht einbettbar (403)",
        404: "Video existiert nicht (404)",
        None: "keine Verbindung zu YouTube",
    }.get(status, f"unerwarteter Status {status}")


def load_songs(path: Path = SONGS_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_song(song: dict) -> str:
    parts = ", ".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in song.items())
    return f"  {{ {parts} }}"


def save_songs(songs: list[dict], path: Path = SONGS_FILE) -> None:
    """Schreibt songs.json mit einem Song pro Zeile (gut lesbare Git-Diffs)."""
    body = ",\n".join(_dump_song(s) for s in songs)
    path.write_text(f"[\n{body}\n]\n" if songs else "[]\n", encoding="utf-8")
