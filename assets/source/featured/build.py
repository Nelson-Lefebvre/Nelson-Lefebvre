"""Build the featured-project images of the profile README.

Layout: KPI screenshot on the left, pipeline diagram top right, data model bottom right.
Run from the repo root: uv run --with pillow python assets/source/featured/build.py
"""
import base64
import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "projects"
PROJECTS = {"alberta": "alberta-executive.png", "calgary-311": "calgary-311-monthly.png"}
WIDTH, PAD, GAP, INNER, BORDER = 2400, 30, 30, 24, "#D0D7DE"


def render(mmd: Path) -> Image.Image:
    # mermaid.ink renders the public diagram source; no local Chromium needed
    # the renderer has no Segoe UI and falls back to serif; arial keeps the repo's sans look
    src = mmd.read_text(encoding="utf-8").replace("Segoe UI, system-ui, sans-serif", "arial")
    code = base64.urlsafe_b64encode(src.encode()).decode()
    url = f"https://mermaid.ink/img/{code}?type=png&bgColor=FFFFFF&width=1400"
    req = urllib.request.Request(url, headers={"User-Agent": "readme-build"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def paste_fit(canvas: Image.Image, img: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    ImageDraw.Draw(canvas).rectangle([x, y, x + w - 1, y + h - 1], outline=BORDER, width=2)
    scale = min((w - 2 * INNER) / img.width, (h - 2 * INNER) / img.height)
    fit = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    canvas.paste(fit, (x + (w - fit.width) // 2, y + (h - fit.height) // 2))


for name, screenshot in PROJECTS.items():
    kpi = Image.open(OUT / screenshot).convert("RGB")
    left_w = round((WIDTH - 2 * PAD - GAP) * 0.58)
    right_w = WIDTH - 2 * PAD - GAP - left_w
    left_h = round(left_w * kpi.height / kpi.width) + 2 * INNER
    right_h = (left_h - GAP) // 2
    canvas = Image.new("RGB", (WIDTH, left_h + 2 * PAD), "white")
    paste_fit(canvas, kpi, (PAD, PAD, left_w, left_h))
    right_x = PAD + left_w + GAP
    paste_fit(canvas, render(HERE / f"{name}-pipeline.mmd"), (right_x, PAD, right_w, right_h))
    paste_fit(canvas, render(HERE / f"{name}-model.mmd"), (right_x, PAD + right_h + GAP, right_w, right_h))
    canvas.save(OUT / f"{name}-overview.png", optimize=True)
    print(name, canvas.size)
