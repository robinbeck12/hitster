# ZeitHit

Musik-Zeitleistenspiel als PWA: Der QR-Code einer Spielkarte wird gescannt, der Song
läuft über den YouTube-Player (Video bleibt verdeckt), „Auflösen" zeigt Jahr, Titel und
Interpret. Das Einsortieren der Songs in die Zeitleiste passiert am Tisch, nicht in der App.

Veröffentlicht unter: <https://robinbeck12.github.io/hitster/>

## Lokal testen

1. In VS Code den Task **Server starten** ausführen (`python -m http.server 8000`).
2. Im Browser `http://localhost:8000` öffnen (die Kamera funktioniert auf `localhost`).
3. Zum Test am iPhone immer die veröffentlichte HTTPS-Seite verwenden.

## Projektstand

Die Umsetzung läuft in Phasen (siehe `CLAUDE.md`, Abschnitt 12).

## Hinweis zu YouTube

Das Verdecken des Players ist für den privaten Gebrauch gedacht. Die YouTube-Richtlinien
verlangen grundsätzlich einen sichtbaren Player.
