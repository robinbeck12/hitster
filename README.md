# ZeitHit

Musik-Zeitleistenspiel als PWA: Der QR-Code einer Spielkarte wird gescannt, der Song
läuft über den YouTube-Player (Video bleibt verdeckt), „Auflösen" zeigt Jahr, Titel und
Interpret. Das Einsortieren der Songs in die Zeitleiste passiert am Tisch, nicht in der App.

Veröffentlicht unter: <https://robinbeck12.github.io/hitster/>

## Lokal testen

1. In VS Code den Task **Server starten** ausführen (`python -m http.server 8000`).
2. Im Browser `http://localhost:8000` öffnen (die Kamera funktioniert auf `localhost`).
3. Zum Test am iPhone immer die veröffentlichte HTTPS-Seite verwenden.

## Karten drucken

Einmalig die Python-Umgebung einrichten (Python 3 nötig):

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r tools/requirements.txt   # macOS/Linux: .venv/bin/python
```

Karten erzeugen (Ausgabe: `cards/cards.pdf`, wird nicht ins Repo committet):

```bash
python tools/make_cards.py              # alle Songs mit echter YouTube-ID
python tools/make_cards.py --ids 1-24   # nur bestimmte IDs, z. B. 1-12,30
python tools/make_cards.py --test       # Testseite mit Beispieldaten (cards/test.pdf)
```

- Karte: 60 × 60 mm, 3 mm Beschnitt, 12 Karten pro A4-Seite (3 × 4) mit Schnittmarken an den Ecken.
- Das PDF enthält abwechselnd eine Seite Vorderseiten (QR-Code) und eine Seite Rückseiten
  (Jahr, Titel, Interpret).
- Drucken: **doppelseitig, „an der langen Kante wenden"**, Skalierung **100 %** (nicht „an Seite anpassen").
  Die Rückseiten sind dafür pro Reihe gespiegelt angeordnet.
- Songs ohne echte YouTube-ID (`TODO`) werden übersprungen und gemeldet.

## Projektstand

Die Umsetzung läuft in Phasen (siehe `CLAUDE.md`, Abschnitt 12).

## Hinweis zu YouTube

Das Verdecken des Players ist für den privaten Gebrauch gedacht. Die YouTube-Richtlinien
verlangen grundsätzlich einen sichtbaren Player.
