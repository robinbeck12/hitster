"""Erzeugt die App-Icons (180, 192, 512 px) im Style-Schema von ZeitHit (Schwarz/Rot).

Aufruf: python tools/make_icons.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

BG = (7, 6, 7)  # --bg
PRIMARY = (196, 22, 28)  # --primary
GLOW = (120, 10, 16)

SIZES = [180, 192, 512]
SUPERSAMPLE = 4
OUT_DIR = Path(__file__).resolve().parent.parent / "icons"


def draw_icon(size: int) -> Image.Image:
    s = size * SUPERSAMPLE
    c = s / 2
    img = Image.new("RGB", (s, s), BG)

    # dunkelrotes Glimmen hinter dem Motiv
    glow = Image.new("RGB", (s, s), BG)
    gd = ImageDraw.Draw(glow)
    r_glow = s * 0.36
    gd.ellipse([c - r_glow, c - r_glow, c + r_glow, c + r_glow], fill=GLOW)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(s * 0.12)), 0.9)

    d = ImageDraw.Draw(img)
    # dünner roter Ring
    r_ring = s * 0.33
    d.ellipse(
        [c - r_ring, c - r_ring, c + r_ring, c + r_ring],
        outline=PRIMARY,
        width=round(s * 0.018),
    )
    # rotes Play-Dreieck (optisch leicht nach rechts versetzt)
    tri_h = s * 0.27
    tri_w = tri_h * 0.88
    x0 = c - tri_w / 2 + s * 0.025
    d.polygon([(x0, c - tri_h / 2), (x0, c + tri_h / 2), (x0 + tri_w, c)], fill=PRIMARY)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for size in SIZES:
        path = OUT_DIR / f"icon-{size}.png"
        draw_icon(size).save(path, optimize=True)
        print(f"geschrieben: {path.relative_to(OUT_DIR.parent)}")


if __name__ == "__main__":
    main()
