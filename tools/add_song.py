"""Fügt einen Song per YouTube-URL zu songs.json hinzu.

Aufruf:
    python tools/add_song.py <youtube-url> <jahr> [--start 12]

Das Skript prüft per oEmbed, ob das Video existiert und einbettbar ist, schlägt Titel und
Interpret aus dem Videotitel vor und lässt dich bestätigen oder ändern. Der Song bekommt
die nächste freie ID; ein vorhandener Platzhalter (yt = "TODO") wird dabei zuerst belegt.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from _common import (
    SONGS_FILE,
    extract_video_id,
    load_songs,
    oembed,
    save_songs,
    status_text,
)

# Zusätze im Videotitel, die nicht zum Songtitel gehören
_NOISE = re.compile(
    r"\s*[\(\[]\s*(?:official|offizielles?|lyrics?|lyric video|audio|hd|hq|4k|remaster(?:ed)?|"
    r"music video|musikvideo|video|live)[^\)\]]*[\)\]]",
    re.IGNORECASE,
)


def suggest(video_title: str, author: str) -> tuple[str, str]:
    """Schlägt (Titel, Interpret) vor: "Interpret - Titel" wird aufgeteilt."""
    cleaned = _NOISE.sub("", video_title).strip()
    if " - " in cleaned:
        artist, title = cleaned.split(" - ", 1)
        return title.strip(), artist.strip()
    author = re.sub(r"\s*(?:- Topic|VEVO)$", "", author, flags=re.IGNORECASE).strip()
    return cleaned, author


def ask(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def next_slot(songs: list[dict]) -> tuple[str, int | None]:
    """Liefert (neue ID, Index des zu ersetzenden Platzhalters oder None)."""
    for i, s in enumerate(songs):
        if s.get("yt") == "TODO":
            return s["id"], i
    highest = max((int(s["id"]) for s in songs), default=0)
    if highest >= 999:
        sys.exit("Fehler: IDs sind dreistellig, es gibt keine freie ID über 999 mehr.")
    return f"{highest + 1:03d}", None


def main() -> int:
    ap = argparse.ArgumentParser(description="Song per YouTube-URL hinzufügen")
    ap.add_argument("url", help="YouTube-URL (oder 11-stellige Video-ID)")
    ap.add_argument("year", type=int, help="Erscheinungsjahr")
    ap.add_argument("--start", type=int, default=0, help="Startsekunde (Intro überspringen)")
    ap.add_argument("--title", help="Titel setzen (überspringt die Rückfrage)")
    ap.add_argument("--artist", help="Interpret setzen (überspringt die Rückfrage)")
    ap.add_argument("--yes", action="store_true", help="Vorschläge ohne Rückfrage übernehmen")
    ap.add_argument("--songs", type=Path, default=SONGS_FILE, help="Pfad zur songs.json")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if not 1900 <= args.year <= date.today().year + 1:
        return fail(f"Unplausibles Jahr: {args.year}")
    if args.start < 0:
        return fail("--start darf nicht negativ sein")

    video_id = extract_video_id(args.url)
    if not video_id:
        return fail("Keine YouTube-Video-ID in der URL gefunden.")

    songs = load_songs(args.songs)
    duplicate = next((s for s in songs if s.get("yt") == video_id), None)
    if duplicate:
        return fail(f"Dieses Video ist schon eingetragen (Karte {duplicate['id']}: {duplicate['title']}).")

    status, data = oembed(video_id)
    print(f"Prüfung: {status_text(status)}")
    if status != 200:
        if status in (401, 403):
            return fail("Das Video darf nicht eingebettet werden. Bitte eine andere Version suchen.")
        if status == 404:
            return fail("Das Video existiert nicht (oder ist privat/gelöscht).")
        return fail("YouTube war nicht erreichbar. Internetverbindung prüfen und erneut versuchen.")

    title, artist = suggest(data.get("title", ""), data.get("author_name", ""))
    print(f"Videotitel: {data.get('title')}  (Kanal: {data.get('author_name')})")

    interactive = not args.yes and sys.stdin.isatty()
    if args.title is None:
        title = ask("Titel", title) if interactive else title
    else:
        title = args.title
    if args.artist is None:
        artist = ask("Interpret", artist) if interactive else artist
    else:
        artist = args.artist
    if not title or not artist:
        return fail("Titel und Interpret dürfen nicht leer sein.")

    new_id, replace_at = next_slot(songs)
    song = {"id": new_id, "yt": video_id, "start": args.start, "title": title, "artist": artist, "year": args.year}

    if interactive:
        print(f"\n  Karte {new_id}: {artist} – {title} ({args.year}), Start bei {args.start} s")
        if input("Eintragen? [J/n]: ").strip().lower() in ("n", "nein"):
            print("Abgebrochen.")
            return 1

    if replace_at is not None:
        songs[replace_at] = song
    else:
        songs.append(song)
    save_songs(songs, args.songs)
    print(f"Eingetragen als Karte {new_id}: {artist} – {title} ({args.year})")
    return 0


def fail(message: str) -> int:
    print(f"Fehler: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
