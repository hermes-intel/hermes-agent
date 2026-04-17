#!/usr/bin/env python3
"""
Hermes ID — Card Image Generator

Generates a shareable AI Identification Card PNG from LLM scoring output.
Uses Pillow for rendering. Downloads Google Fonts on first run.

Usage:
    python3 generate_card.py <score.json> <output.png>
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
LGRAY = (230, 230, 230)

# ── Layout ──────────────────────────────────────────────────────────
IMG_W, IMG_H = 640, 810
CARD_X, CARD_Y = 30, 28
CARD_W, CARD_H = 580, 700
PAD = 24
RADIUS = 24

# Avatar sits on left; title + fields sit on right — like a real ID card
AVATAR_W, AVATAR_H = 190, 250
AVATAR_X = CARD_X + PAD
AVATAR_Y = CARD_Y + 40

RIGHT_X = AVATAR_X + AVATAR_W + 18   # right column left edge
RIGHT_W = CARD_X + CARD_W - PAD - RIGHT_X  # right column width


def _h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


# ── Font Management ─────────────────────────────────────────────────
FONT_DIR = Path.home() / ".hermes" / "cache" / "fonts"

FONT_URLS = {
    "PermanentMarker-Regular.ttf":
        "https://github.com/google/fonts/raw/main/apache/"
        "permanentmarker/PermanentMarker-Regular.ttf",
    "Caveat-Bold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/"
        "caveat/static/Caveat-Bold.ttf",
    "Inter_18pt-Regular.ttf":
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-Regular.ttf",
    "Inter_18pt-Bold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-Bold.ttf",
    "Inter_18pt-SemiBold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/"
        "inter/static/Inter_18pt-SemiBold.ttf",
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
    key = f"{style}:{sz}"
    if key in _cache:
        return _cache[key]
    path = _dl(STYLES.get(style, STYLES["body"]))
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


def rtext(d: ImageDraw.ImageDraw, txt: str, x: int, y: int, max_w: int, f, fill):
    """Draw text right-aligned within a box starting at x with width max_w."""
    w = tw(d, txt, f)
    d.text((x + max_w - w, y), txt, fill=fill, font=f)


# ── Avatar ──────────────────────────────────────────────────────────
def draw_avatar(d: ImageDraw.ImageDraw, handle: str,
                x: int, y: int, w: int, h: int):
    hv = _h(handle)
    h1 = (hv % 360) / 360.0
    h2 = ((hv * 13) % 360) / 360.0
    r1, g1, b1 = (int(c * 255) for c in colorsys.hls_to_rgb(h1, 0.20, 0.28))
    r2, g2, b2 = (int(c * 255) for c in colorsys.hls_to_rgb(h2, 0.28, 0.32))

    # ── double border frame ──
    d.rectangle([x, y, x + w, y + h], outline=BLUE, width=3)
    d.rectangle([x + 5, y + 5, x + w - 5, y + h - 5], outline=BLUE, width=2)

    ix, iy = x + 8, y + 8
    iw, ih = w - 16, h - 16

    # ── gradient background ──
    for band in range(ih):
        t = band / max(ih - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        d.line([(ix, iy + band), (ix + iw, iy + band)], fill=(r, g, b))

    # ── halftone dots ──
    for dy in range(0, ih, 5):
        for dx in range(0, iw, 5):
            bright = 30 + int((dy / ih) * 30)
            d.ellipse(
                [ix + dx + 1, iy + dy + 1, ix + dx + 3, iy + dy + 3],
                fill=(min(255, r1 + bright), min(255, g1 + bright),
                      min(255, b1 + bright)),
            )

    # ── manga character silhouette ──
    cx = ix + iw // 2
    head_cy = iy + ih * 28 // 100
    head_r = iw // 4
    body_top = head_cy + head_r

    shade = (max(0, r1 - 40), max(0, g1 - 40), max(0, b1 - 40))
    shade2 = (max(0, r1 - 25), max(0, g1 - 25), max(0, b1 - 25))
    spike = (max(0, r1 - 55), max(0, g1 - 55), max(0, b1 - 55))

    # Hair spikes (multiple, manga style)
    spikes_data = [
        (cx - 18, head_cy - head_r, cx - 28, head_cy - head_r - 35),
        (cx - 8,  head_cy - head_r - 3, cx - 12, head_cy - head_r - 42),
        (cx + 2,  head_cy - head_r - 4, cx - 2,  head_cy - head_r - 48),
        (cx + 12, head_cy - head_r - 2, cx + 8,  head_cy - head_r - 38),
        (cx + 20, head_cy - head_r + 2, cx + 30, head_cy - head_r - 28),
        (cx - 24, head_cy - head_r + 5, cx - 36, head_cy - head_r - 20),
        (cx + 26, head_cy - head_r + 8, cx + 38, head_cy - head_r - 12),
    ]
    for x1, y1, x2, y2 in spikes_data:
        d.line([(x1, y1), (x2, y2)], fill=spike, width=4)
        d.line([(x1 + 1, y1), (x2 + 2, y2 + 3)], fill=shade, width=2)

    # Head
    d.ellipse([cx - head_r, head_cy - head_r,
               cx + head_r, head_cy + head_r], fill=shade)
    # Face detail (jaw line)
    d.arc([cx - head_r + 4, head_cy - 4,
           cx + head_r - 4, head_cy + head_r + 8],
          30, 150, fill=shade2, width=2)
    # Eye hints
    ey = head_cy + 2
    d.ellipse([cx - 12, ey - 3, cx - 5, ey + 3],
              fill=(min(255, r1 + 60), min(255, g1 + 60), min(255, b1 + 60)))
    d.ellipse([cx + 5, ey - 3, cx + 12, ey + 3],
              fill=(min(255, r1 + 60), min(255, g1 + 60), min(255, b1 + 60)))

    # Neck
    d.rectangle([cx - 8, body_top, cx + 8, body_top + 12], fill=shade2)

    # Shoulders and body
    d.polygon([
        (cx - iw // 2 + 5, iy + ih),
        (cx - iw // 3, body_top + 25),
        (cx - 10, body_top + 14),
        (cx + 10, body_top + 14),
        (cx + iw // 3, body_top + 25),
        (cx + iw // 2 - 5, iy + ih),
    ], fill=shade2)
    # Collar/clothing line
    d.line([(cx - 10, body_top + 14), (cx, body_top + 28)], fill=shade, width=2)
    d.line([(cx + 10, body_top + 14), (cx, body_top + 28)], fill=shade, width=2)

    # ── scan lines for manga texture ──
    for sy in range(0, ih, 3):
        d.line([(ix, iy + sy), (ix + iw, iy + sy)],
               fill=(min(255, r1 + 8), min(255, g1 + 8), min(255, b1 + 8)))


# ── Barcode ─────────────────────────────────────────────────────────
def draw_barcode(d: ImageDraw.ImageDraw, handle: str,
                 x: int, y: int, max_w: int, h: int):
    hv = _h(handle)
    cur = x
    idx = 0
    while cur < x + max_w and idx < 60:
        bit = hv & 1
        bw = 2.5 if bit else 1.0
        d.rectangle([cur, y, cur + bw, y + h], fill=BLACK)
        cur += bw + 0.8
        hv >>= 1
        if hv == 0:
            hv = _h(handle + str(idx))
        idx += 1


# ── Main Card Generator ────────────────────────────────────────────
def generate(data: dict, out_path: str) -> str:
    img = Image.new("RGB", (IMG_W, IMG_H), BLUE)
    d = ImageDraw.Draw(img)

    # ── white card ──
    d.rounded_rectangle(
        [CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H],
        radius=RADIUS, fill=WHITE,
    )

    lx = CARD_X + PAD
    rx = CARD_X + CARD_W - PAD

    # ── top bar ──
    d.text((lx, CARD_Y + 14),
           "loading / hermes intel ai scorecard",
           fill=GRAY, font=F(10))
    w_hi = tw(d, "**Hermes Intel", F(10, "semi"))
    d.text((rx - w_hi, CARD_Y + 14),
           "**Hermes Intel", fill=BLUE, font=F(10, "semi"))

    # ── avatar (left side, extends tall) ──
    draw_avatar(d, data["handle"], AVATAR_X, AVATAR_Y, AVATAR_W, AVATAR_H)

    # ── right column: title + fields + proficiencies ──
    ry = AVATAR_Y + 2

    # Quote mark
    d.text((RIGHT_X - 4, ry - 6), "\u201C", fill=BLUE, font=F(32, "title"))

    # "AI IDENTIFICATION CARD" — large graffiti title
    ry += 16
    tf = F(34, "title")
    for line in ("AI", "IDENTIFICATION", "CARD"):
        d.text((RIGHT_X, ry), line, fill=BLUE, font=tf)
        ry += 38
    # Closing quote
    last_w = tw(d, "CARD", tf)
    d.text((RIGHT_X + last_w + 6, ry - 34), "\u201D", fill=BLUE, font=F(32, "title"))

    # ── info fields (right column) ──
    ry += 14
    fb = F(16, "bold")
    fr = F(16, "semi")
    fs = F(21, "bold")

    fields = [
        ("[name]", f"@{data['handle']}", fr),
        ("[AI Score]", f"{data['total_score']}/100", fs),
        ("[Level]", data["level"], fr),
        ("[Role*]", data["role"], fr),
    ]
    for label, val, vf in fields:
        d.text((RIGHT_X, ry), label, fill=BLACK, font=fb)
        rtext(d, val, RIGHT_X, ry, RIGHT_W, vf, BLACK)
        ry += 30

    # ── proficiencies (below avatar+fields, full width) ──
    prof_y = max(ry + 12, AVATAR_Y + AVATAR_H + 18)
    d.text((lx, prof_y), "[AI Proficiencies]", fill=BLACK, font=fb)
    prof_y += 26

    dims = data.get("dimensions", [])
    top4 = sorted(dims, key=lambda x: x["score"], reverse=True)[:4]
    pf = F(15, "body")
    psf = F(15, "bold")
    for dim in top4:
        d.text((lx + 12, prof_y), dim["name"], fill=DARK, font=pf)
        sw = tw(d, str(dim["score"]), psf)
        d.text((rx - sw, prof_y), str(dim["score"]), fill=BLACK, font=psf)
        prof_y += 26

    # ── bottom section ──
    by = CARD_Y + CARD_H - 68

    # "Hermes Agent" cursive
    d.text((lx, by), "Hermes Agent", fill=BLUE, font=F(30, "cursive"))

    # Barcode
    draw_barcode(d, data["handle"], rx - 200, by + 6, 200, 26)

    # Divider
    d.line([(lx, by + 40), (rx, by + 40)], fill=LGRAY, width=1)

    # Credits
    sf = F(10)
    d.text((lx, by + 46),
           "Powered by Hermes Agent \u00b7 Test your AI Native level",
           fill=GRAY, font=sf)
    cred = "X @Hermes_Intel_"
    cw = tw(d, cred, sf)
    d.text((rx - cw, by + 46), cred, fill=GRAY, font=sf)

    # ── footer outside card ──
    ff = F(20, "bold")
    ftxt = "hermesid.wtf"
    d.text(((IMG_W - tw(d, ftxt, ff)) // 2, CARD_Y + CARD_H + 18),
           ftxt, fill=WHITE, font=ff)

    # ── save ──
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Card saved: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_card.py <score.json> <output.png>")
        example = {
            "handle": "teknium", "total_score": 92,
            "level": "Agent God", "role": "Hermes Creator",
            "dimensions": [
                {"name": "AI Usage", "score": 95},
                {"name": "AI Understanding", "score": 93},
                {"name": "Communication", "score": 88},
                {"name": "Product Building", "score": 96},
                {"name": "Adoption Speed", "score": 90},
                {"name": "Prompt Engineering", "score": 85},
                {"name": "Critical Awareness", "score": 82},
                {"name": "Knowledge Sharing", "score": 94},
            ],
            "summary": "A true Agent God who shapes the AI landscape.",
        }
        print(f"\nExample:\n{json.dumps(example, indent=2)}")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)
    generate(data, sys.argv[2])
