"""Prüft alle Einträge in songs.json per YouTube-oEmbed und listet Problemfälle.

Aufruf:
    python tools/check_songs.py

Rückgabecode 0 = alles in Ordnung, 1 = mindestens ein Problem.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from _common import SONGS_FILE, load_songs, oembed, status_text


def check_fields(song: dict, seen_ids: set, seen_yt: dict) -> list[str]:
    problems = []
    sid = song.get("id", "")
    if not re.fullmatch(r"\d{3}", str(sid)):
        problems.append(f"ID {sid!r} ist nicht dreistellig")
    if sid in seen_ids:
        problems.append("ID kommt doppelt vor")
    seen_ids.add(sid)

    year = song.get("year")
    if not isinstance(year, int) or not 1900 <= year <= date.today().year + 1:
        problems.append(f"Jahr unplausibel: {year!r}")
    start = song.get("start", 0)
    if not isinstance(start, int) or start < 0:
        problems.append(f"start ungültig: {start!r}")
    if not str(song.get("title", "")).strip():
        problems.append("Titel fehlt")
    if not str(song.get("artist", "")).strip():
        problems.append("Interpret fehlt")

    yt = song.get("yt")
    if yt and yt != "TODO":
        if yt in seen_yt:
            problems.append(f"Video doppelt (auch Karte {seen_yt[yt]})")
        seen_yt[yt] = sid
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="songs.json prüfen")
    ap.add_argument("--songs", type=Path, default=SONGS_FILE, help="Pfad zur songs.json")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    songs = load_songs(args.songs)
    seen_ids, seen_yt = set(), {}
    placeholders = 0
    issues: list[tuple[str, str]] = []
    checked = 0

    for song in songs:
        sid = song.get("id", "?")
        problems = check_fields(song, seen_ids, seen_yt)
        yt = song.get("yt")

        if not yt or yt == "TODO":
            placeholders += 1
            print(f"{sid}  Platzhalter (yt = TODO), wird übersprungen")
        else:
            status, _ = oembed(yt)
            checked += 1
            if status == 200:
                print(f"{sid}  ok  {song.get('artist')} – {song.get('title')}")
            else:
                problems.append(f"Video: {status_text(status)}")

        for p in problems:
            issues.append((sid, p))
            print(f"{sid}  PROBLEM: {p}")

    print(f"\n{len(songs)} Einträge, {checked} online geprüft, {placeholders} Platzhalter, {len(issues)} Problem(e)")
    if issues:
        print("\nProblemfälle:")
        for sid, p in issues:
            print(f"  {sid}: {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
