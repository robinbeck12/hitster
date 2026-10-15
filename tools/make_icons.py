"""Erzeugt die App-Icons (180, 192, 512 px) im Style-Schema von ZeitHit.

Aufruf: python tools/make_icons.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

BG = (15, 11, 30)  # --bg
PRIMARY = (255, 46, 147)  # --primary
SECONDARY = (0, 229, 255)  # --secondary
ACCENT = (255, 212, 0)  # --accent

SIZES = [180, 192, 512]
SUPERSAMPLE = 4
OUT_DIR = Path(__file__).resolve().parent.parent / "icons"


def draw_icon(size: int) -> Image.Image:
    s = size * SUPERSAMPLE
    img = Image.new("RGB", (s, s), BG)
    d = ImageDraw.Draw(img)
    c = s / 2

    # Cyan-Ring als Zeitleisten-/Schallplatten-Andeutung
    r_ring = s * 0.40
    ring_w = s * 0.035
    d.ellipse(
        [c - r_ring, c - r_ring, c + r_ring, c + r_ring],
        outline=SECONDARY,
        width=round(ring_w),
    )

    # Magenta-Scheibe
    r_disc = s * 0.31
    d.ellipse([c - r_disc, c - r_disc, c + r_disc, c + r_disc], fill=PRIMARY)

    # Gelbes Play-Dreieck (optisch leicht nach rechts versetzt)
    tri_h = s * 0.26
    tri_w = tri_h * 0.88
    x0 = c - tri_w / 2 + s * 0.02
    d.polygon(
        [(x0, c - tri_h / 2), (x0, c + tri_h / 2), (x0 + tri_w, c)],
        fill=ACCENT,
    )

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for size in SIZES:
        path = OUT_DIR / f"icon-{size}.png"
        draw_icon(size).save(path, optimize=True)
        print(f"geschrieben: {path.relative_to(OUT_DIR.parent)}")


if __name__ == "__main__":
    main()
