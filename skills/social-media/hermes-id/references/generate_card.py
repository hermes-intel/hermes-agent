#!/usr/bin/env python3
"""
Hermes ID — Card Image Generator

Generates a shareable AI Identification Card PNG from LLM scoring output.
Uses Pillow for rendering. Downloads Google Fonts on first run.

Usage:
    python3 generate_card.py <score.json> <output.png>

Input JSON format:
{
    "handle": "teknium",
    "total_score": 92,
    "level": "Agent God",
    "role": "Hermes Creator",
    "dimensions": [
        {"name": "AI Usage", "score": 95, "justification": "..."},
        ...
    ],
    "summary": "A one-sentence summary."
}
"""

from __future__ import annotations

import json
import sys
import os
import hashlib
import colorsys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ImageDraw, ImageFont

# ── Colors ──────────────────────────────────────────────────────────
BLUE = (43, 92, 230)
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
DARK = (51, 51, 51)
GRAY = (136, 136, 136)
LGRAY = (238, 238, 238)

# ── Layout ──────────────────────────────────────────────────────────
IMG_W, IMG_H = 640, 880
CARD_X, CARD_Y = 30, 30
CARD_W, CARD_H = 580, 760
PAD = 28
RADIUS = 24


# ── Hashing ─────────────────────────────────────────────────────────
def _h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


# ── Font Management ─────────────────────────────────────────────────
FONT_DIR = Path.home() / ".hermes" / "cache" / "fonts"

FONT_URLS = {
    "PermanentMarker-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/apache/"
        "permanentmarker/PermanentMarker-Regular.ttf"
    ),
    "Caveat-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/"
        "caveat/static/Caveat-Bold.ttf"
    ),
    "Inter_18pt-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-Regular.ttf"
    ),
    "Inter_18pt-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-Bold.ttf"
    ),
    "Inter_18pt-SemiBold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-SemiBold.ttf"
    ),
}

_cache: dict = {}


def _dl(fname: str) -> str | None:
    dest = FONT_DIR / fname
    if dest.exists():
        return str(dest)
    url = FONT_URLS.get(fname)
    if not url:
        return None
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import urllib.request
        urllib.request.urlretrieve(url, str(dest))
        return str(dest)
    except Exception:
        return None


def _sysfont(sz: int):
    for p in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFPro.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                continue
    return ImageFont.load_default(size=sz)


STYLES = {
    "title": "PermanentMarker-Regular.ttf",
    "cursive": "Caveat-Bold.ttf",
    "body": "Inter_18pt-Regular.ttf",
    "bold": "Inter_18pt-Bold.ttf",
    "semi": "Inter_18pt-SemiBold.ttf",
}


def F(sz: int, style: str = "body"):
    """Load a font by style and size, with download + fallback."""
    key = f"{style}:{sz}"
    if key in _cache:
        return _cache[key]
    fname = STYLES.get(style, STYLES["body"])
    path = _dl(fname)
    if path:
        try:
            f = ImageFont.truetype(path, sz)
            _cache[key] = f
            return f
        except Exception:
            pass
    f = _sysfont(sz)
    _cache[key] = f
    return f


# ── Drawing Helpers ─────────────────────────────────────────────────
def tw(d: ImageDraw.ImageDraw, txt: str, f) -> int:
    bb = d.textbbox((0, 0), txt, font=f)
    return bb[2] - bb[0]


def rtext(d: ImageDraw.ImageDraw, txt: str, y: int, f, fill, rx: int):
    d.text((rx - tw(d, txt, f), y), txt, fill=fill, font=f)


def avatar(d: ImageDraw.ImageDraw, handle: str, x: int, y: int, w: int, h: int):
    """Draw a unique stylized avatar with halftone effect."""
    hv = _h(handle)
    h1 = (hv % 360) / 360.0
    h2 = ((hv * 13) % 360) / 360.0

    r1, g1, b1 = (int(c * 255) for c in colorsys.hls_to_rgb(h1, 0.22, 0.28))
    r2, g2, b2 = (int(c * 255) for c in colorsys.hls_to_rgb(h2, 0.30, 0.32))

    # Double border frame
    d.rectangle([x, y, x + w, y + h], outline=BLUE, width=3)
    d.rectangle([x + 6, y + 6, x + w - 6, y + h - 6], outline=BLUE, width=2)

    # Inner area
    ix, iy = x + 10, y + 10
    iw, ih = w - 20, h - 20

    # Gradient fill via horizontal bands
    for band in range(ih):
        t = band / max(ih - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        d.line([(ix, iy + band), (ix + iw, iy + band)], fill=(r, g, b))

    # Halftone dot pattern
    for dy in range(0, ih, 6):
        for dx in range(0, iw, 6):
            lum = 40 + (dy * 20 // ih)
            d.ellipse(
                [ix + dx + 1, iy + dy + 1, ix + dx + 3, iy + dy + 3],
                fill=(
                    min(255, r1 + lum),
                    min(255, g1 + lum),
                    min(255, b1 + lum),
                ),
            )

    # Head silhouette
    cx = ix + iw // 2
    cy = iy + ih * 3 // 10
    hr = min(iw, ih) // 5
    head_col = (max(0, r1 - 35), max(0, g1 - 35), max(0, b1 - 35))
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=head_col)

    # Hair spikes
    spike_col = (max(0, r1 - 50), max(0, g1 - 50), max(0, b1 - 50))
    offsets = [(-12, -20), (-3, -28), (10, -18), (-8, -15), (6, -24)]
    for ox, oy in offsets:
        sx = cx + ox
        d.line([(sx, cy - hr), (sx + ox // 2, cy - hr + oy)], fill=spike_col, width=3)

    # Shoulders
    st = cy + hr
    shoulder_col = (max(0, r1 - 25), max(0, g1 - 25), max(0, b1 - 25))
    d.polygon(
        [
            (cx - iw // 3, iy + ih),
            (cx - hr + 5, st + 8),
            (cx + hr - 5, st + 8),
            (cx + iw // 3, iy + ih),
        ],
        fill=shoulder_col,
    )

    # Scan lines (for retro/manga feel)
    for sy in range(0, ih, 3):
        d.line(
            [(ix, iy + sy), (ix + iw, iy + sy)],
            fill=(
                min(255, r1 + 10),
                min(255, g1 + 10),
                min(255, b1 + 10),
            ),
            width=1,
        )


def barcode(d: ImageDraw.ImageDraw, handle: str, x: int, y: int, max_w: int, h: int):
    """Draw a decorative barcode derived from the handle."""
    hv = _h(handle)
    cur = x
    idx = 0
    while cur < x + max_w and idx < 50:
        bit = hv & 1
        bw = 3 if bit else 1.5
        d.rectangle([cur, y, cur + bw, y + h], fill=BLACK)
        cur += bw + 1.2
        hv >>= 1
        if hv == 0:
            hv = _h(handle + str(idx))
        idx += 1


# ── Main Card Generator ────────────────────────────────────────────
def generate(data: dict, out_path: str) -> str:
    img = Image.new("RGB", (IMG_W, IMG_H), BLUE)
    d = ImageDraw.Draw(img)

    # White card
    d.rounded_rectangle(
        [CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H],
        radius=RADIUS,
        fill=WHITE,
    )

    lx = CARD_X + PAD
    rx = CARD_X + CARD_W - PAD

    # ── Top bar ──
    d.text(
        (lx, CARD_Y + 18),
        "loading / hermes intel ai scorecard",
        fill=GRAY,
        font=F(11),
    )
    rtext(d, "**Hermes Intel", CARD_Y + 18, F(11, "semi"), BLUE, rx)

    # ── Avatar + Title ──
    av_y = CARD_Y + 48
    avatar(d, data["handle"], lx, av_y, 170, 200)

    tx = lx + 190
    ty = CARD_Y + 52

    # Opening quote mark
    d.text((tx, ty - 8), "\u275D", fill=BLUE, font=F(28, "title"))
    ty += 22

    # "AI IDENTIFICATION CARD"
    tf = F(36, "title")
    for line in ("AI", "IDENTIFICATION", "CARD"):
        d.text((tx, ty), line, fill=BLUE, font=tf)
        ty += 42

    # Closing quote mark
    qtw = tw(d, "CARD", tf)
    d.text((tx + qtw + 8, ty - 38), "\u275E", fill=BLUE, font=F(28, "title"))

    # ── Info fields ──
    fy = av_y + 218
    fb = F(16, "bold")
    fr = F(16, "body")
    fs = F(21, "bold")

    fields = [
        ("[name]", f"@{data['handle']}", fr),
        ("[AI Score]", f"{data['total_score']}/100", fs),
        ("[Level]", data["level"], fr),
        ("[Role*]", data["role"], fr),
    ]
    for label, val, vf in fields:
        d.text((lx, fy), label, fill=BLACK, font=fb)
        rtext(d, val, fy, vf, BLACK, rx)
        fy += 32

    # ── AI Proficiencies ──
    fy += 10
    d.text((lx, fy), "[AI Proficiencies]", fill=BLACK, font=fb)
    fy += 28

    dims = data.get("dimensions", [])
    top4 = sorted(dims, key=lambda x: x["score"], reverse=True)[:4]
    pf = F(15, "body")
    psf = F(15, "bold")
    for dim in top4:
        d.text((lx + 14, fy), dim["name"], fill=DARK, font=pf)
        rtext(d, str(dim["score"]), fy, psf, BLACK, rx)
        fy += 27

    # ── Bottom section ──
    by = CARD_Y + CARD_H - 72

    # "Hermes Agent" cursive
    d.text((lx, by), "Hermes Agent", fill=BLUE, font=F(32, "cursive"))

    # Barcode
    barcode(d, data["handle"], lx + 310, by + 6, 200, 26)

    # Divider line
    d.line([(lx, by + 42), (rx, by + 42)], fill=LGRAY, width=1)

    # Credits
    sf = F(11)
    d.text(
        (lx, by + 48),
        "Powered by Hermes Agent \u00b7 Test your AI Native level",
        fill=GRAY,
        font=sf,
    )
    rtext(d, "X @Hermes_Intel_", by + 48, sf, GRAY, rx)

    # ── Footer (outside card) ──
    ff = F(20, "bold")
    ftxt = "hermesid.wtf"
    d.text(((IMG_W - tw(d, ftxt, ff)) // 2, CARD_Y + CARD_H + 16), ftxt, fill=WHITE, font=ff)

    # ── Save ──
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Card saved: {out_path}")
    return out_path


# ── CLI Entry Point ─────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_card.py <score.json> <output.png>")
        print()
        print("Example score.json:")
        print(json.dumps({
            "handle": "teknium",
            "total_score": 92,
            "level": "Agent God",
            "role": "Hermes Creator",
            "dimensions": [
                {"name": "AI Usage", "score": 95, "justification": "..."},
                {"name": "AI Understanding", "score": 90, "justification": "..."},
                {"name": "Communication", "score": 88, "justification": "..."},
                {"name": "Product Building", "score": 92, "justification": "..."},
                {"name": "Adoption Speed", "score": 85, "justification": "..."},
                {"name": "Prompt Engineering", "score": 80, "justification": "..."},
                {"name": "Critical Awareness", "score": 78, "justification": "..."},
                {"name": "Knowledge Sharing", "score": 90, "justification": "..."},
            ],
            "summary": "A true Agent God who shapes the AI landscape.",
        }, indent=2))
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    generate(data, sys.argv[2])


if __name__ == "__main__":
    main()
