from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assets_dir = os.path.join(repo_root, "assets")
    _ensure_dir(assets_dir)

    out_path = os.path.join(assets_dir, "sample_road.png")
    if os.path.exists(out_path):
        print(f"Already exists: {out_path}")
        return

    # Create a simple "road-ish" texture with a few bright crack-like lines.
    w, h = 768, 432
    img = Image.new("RGB", (w, h), (20, 24, 32))
    d = ImageDraw.Draw(img)

    # Subtle lane-ish stripes
    for x in range(40, w, 140):
        d.rectangle([x, 0, x + 10, h], fill=(28, 32, 42))

    # Cracks
    crack_color = (220, 220, 220)
    d.line((60, 40, 320, 180, 520, 130, 710, 260), fill=crack_color, width=3)
    d.line((120, 360, 250, 260, 410, 300, 590, 220), fill=crack_color, width=2)
    d.line((500, 20, 560, 120, 610, 80, 680, 160), fill=crack_color, width=2)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img.save(out_path)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()

