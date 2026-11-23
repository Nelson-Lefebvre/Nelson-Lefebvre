"""Build the featured-project images of the profile README.

Layout: KPI screenshot on the left, pipeline diagram top right, data model bottom right.
Run from the repo root: uv run --with pillow python assets/source/featured/build.py
"""
import base64
import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "projects"
PROJECTS = {"alberta": "alberta-executive.png", "calgary-311": "calgary-311-monthly.png"}
WIDTH, GAP = 2400, 40


def render(mmd: Path) -> Image.Image:
    # mermaid.ink renders the public diagram source; no local Chromium needed
    # the renderer has no Segoe UI and falls back to serif; arial keeps the repo's sans look
    src = mmd.read_text(encoding="utf-8").replace("Segoe UI, system-ui, sans-serif", "arial")
    code = base64.urlsafe_b64encode(src.encode()).decode()
    url = f"https://mermaid.ink/img/{code}?type=png&bgColor=FFFFFF&width=1400"
    req = urllib.request.Request(url, headers={"User-Agent": "readme-build"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def trim(img: Image.Image, tol: int = 12, margin: int = 16) -> Image.Image:
    """Crop the uniform margin (colour of the top-left pixel), keeping a thin border so text never touches the edge."""
    bg = Image.new("RGB", img.size, img.getpixel((0, 0)))
    mask = ImageChops.difference(img, bg).convert("L").point(lambda v: 255 if v > tol else 0)
    left, top, right, bottom = mask.getbbox() or (0, 0, *img.size)
    return img.crop((max(left - margin, 0), max(top - margin, 0), min(right + margin, img.width), min(bottom + margin, img.height)))


def scaled(img: Image.Image, width: int) -> Image.Image:
    return img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)


for name, screenshot in PROJECTS.items():
    kpi = trim(Image.open(OUT / screenshot).convert("RGB"))
    pipe = trim(render(HERE / f"{name}-pipeline.mmd"))
    model = trim(render(HERE / f"{name}-model.mmd"))
    # right column width that makes pipeline + model exactly as tall as the screenshot: no empty space
    a_kpi = kpi.width / kpi.height
    k = pipe.height / pipe.width + model.height / model.width
    right_w = round((WIDTH - GAP - a_kpi * GAP) / (1 + a_kpi * k))
    left_w = WIDTH - GAP - right_w
    kpi, pipe, model = scaled(kpi, left_w), scaled(pipe, right_w), scaled(model, right_w)
    canvas = Image.new("RGB", (WIDTH, max(kpi.height, pipe.height + GAP + model.height)), "white")
    canvas.paste(kpi, (0, 0))
    canvas.paste(pipe, (left_w + GAP, 0))
    canvas.paste(model, (left_w + GAP, pipe.height + GAP))
    canvas.save(OUT / f"{name}-overview.png", optimize=True)
    print(name, canvas.size, "right column", right_w)
