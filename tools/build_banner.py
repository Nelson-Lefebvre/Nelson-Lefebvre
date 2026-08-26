"""Rebuild assets/banner.png: the profile photo, cropped to a circle, composited
into the empty left area of the base banner.

Run from the repository root:

    python tools/build_banner.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "source" / "banner-base.jpg"
PHOTO = ROOT / "assets" / "source" / "profile-photo.png"
OUT = ROOT / "assets" / "banner.png"

SS = 8                # supersampling factor, for a smooth circle edge
DIAMETER = 196        # avatar diameter, in banner pixels
CENTRE = (176, 212)   # avatar centre, in banner pixels
RING_W = 7            # white ring thickness
LINE_W = 3            # navy outline thickness
NAVY = (0, 74, 97, 255)    # sampled from the banner title type
WHITE = (255, 255, 255, 255)


def circular_avatar(photo, size):
    """Centre-crop `photo` to a square and mask it into a circle of `size` px."""
    side = min(photo.size)
    photo = photo.crop((
        (photo.width - side) // 2,
        (photo.height - side) // 2,
        (photo.width + side) // 2,
        (photo.height + side) // 2,
    ))
    face = photo.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    return face, mask


def build():
    banner = Image.open(BASE).convert("RGBA")
    photo = Image.open(PHOTO).convert("RGBA")

    outer = DIAMETER + 2 * (RING_W + LINE_W)
    big = outer * SS

    # Navy outline with a white ring inside it, drawn oversized then downscaled.
    plate = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(plate)
    draw.ellipse([0, 0, big - 1, big - 1], fill=NAVY)
    inset = LINE_W * SS
    draw.ellipse([inset, inset, big - 1 - inset, big - 1 - inset], fill=WHITE)

    face, mask = circular_avatar(photo, DIAMETER * SS)
    offset = (RING_W + LINE_W) * SS
    plate.paste(face, (offset, offset), mask)
    plate = plate.resize((outer, outer), Image.LANCZOS)

    banner.alpha_composite(plate, (CENTRE[0] - outer // 2, CENTRE[1] - outer // 2))
    banner.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} {banner.size}")


if __name__ == "__main__":
    build()
