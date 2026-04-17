#!/usr/bin/env python3
"""
Hermes ID — Card Image Generator

Usage:
    python3 generate_card.py <score.json> <output.png> [--avatar <path>]

    Automatically fetches the real X profile picture via unavatar.io (free, no API key).
    Applies a manga-style halftone filter.
    Maps score to title (Agent God, AI Native, etc.).
"""

from __future__ import annotations

import json
import math
import sys
import os
import hashlib
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
except ImportError:
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# ── Colors ──────────────────────────────────────────────────────────
BLUE = (43, 92, 230)
BLUE_LIGHT = (43, 92, 230, 40)
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
DARK = (51, 51, 51)
GRAY = (136, 136, 136)
LGRAY = (225, 225, 225)
BLUE_BG = (220, 228, 255)

# ── Layout ──────────────────────────────────────────────────────────
IMG_W, IMG_H = 640, 1060
CARD_X, CARD_Y = 28, 26
CARD_W, CARD_H = 584, 960
PAD = 26
RADIUS = 24

AVATAR_W, AVATAR_H = 200, 260
AVATAR_X = CARD_X + PAD
AVATAR_Y = CARD_Y + 38

RIGHT_X = AVATAR_X + AVATAR_W + 16
RIGHT_END = CARD_X + CARD_W - PAD

# ── Score → Level mapping (synced with SKILL.md) ────────────────────
LEVEL_MAP = [
    (95, "Agent God"),
    (88, "AI Native"),
    (78, "AI Strategist"),
    (65, "AI Explorer"),
    (50, "AI Curious"),
    (35, "AI Aware"),
    (0,  "AI Normie"),
]

ROLE_MAP = [
    (95, "Hermes Creator"),
    (88, "AI Innovator"),
    (78, "AI Architect"),
    (65, "AI Practitioner"),
    (50, "AI Learner"),
    (0,  "AI Observer"),
]


def score_to_level(score: float) -> str:
    for threshold, label in LEVEL_MAP:
        if score >= threshold:
            return label
    return LEVEL_MAP[-1][1]


def score_to_role(score: float) -> str:
    for threshold, label in ROLE_MAP:
        if score >= threshold:
            return label
    return ROLE_MAP[-1][1]


def _h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


# ── Font Management ─────────────────────────────────────────────────
FONT_DIR = Path.home() / ".hermes" / "cache" / "fonts"
FONT_URLS = {
    "PermanentMarker-Regular.ttf":
        "https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf",
    "Caveat-Bold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Bold.ttf",
    "Inter_18pt-Regular.ttf":
        "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-Regular.ttf",
    "Inter_18pt-Bold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-Bold.ttf",
    "Inter_18pt-SemiBold.ttf":
        "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter_18pt-SemiBold.ttf",
}
_fc: dict = {}


def _dl(fname: str) -> str | None:
    dest = FONT_DIR / fname
    if dest.exists():
        return str(dest)
    url = FONT_URLS.get(fname)
    if not url:
        return None
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(dest))
        return str(dest)
    except Exception:
        return None


def _sf(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                continue
    return ImageFont.load_default(size=sz)


_STYLES = {
    "title": "PermanentMarker-Regular.ttf",
    "cursive": "Caveat-Bold.ttf",
    "body": "Inter_18pt-Regular.ttf",
    "bold": "Inter_18pt-Bold.ttf",
    "semi": "Inter_18pt-SemiBold.ttf",
}


def F(sz: int, style: str = "body"):
    k = f"{style}:{sz}"
    if k in _fc:
        return _fc[k]
    p = _dl(_STYLES.get(style, _STYLES["body"]))
    if p:
        try:
            f = ImageFont.truetype(p, sz)
            _fc[k] = f
            return f
        except Exception:
            pass
    f = _sf(sz)
    _fc[k] = f
    return f


def tw(d, txt, f):
    bb = d.textbbox((0, 0), txt, font=f)
    return bb[2] - bb[0]


def th(d, txt, f):
    bb = d.textbbox((0, 0), txt, font=f)
    return bb[3] - bb[1]


# ── Avatar ──────────────────────────────────────────────────────────
def fetch_x_avatar(handle: str) -> str | None:
    cache_dir = Path.home() / ".hermes" / "cache" / "avatars"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{handle}.jpg"
    if cached.exists() and cached.stat().st_size > 1000:
        return str(cached)

    url = f"https://unavatar.io/x/{handle}"
    print(f"  Fetching avatar: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesID/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        if len(data) > 500:
            cached.write_bytes(data)
            return str(cached)
    except Exception as e:
        print(f"  Avatar fetch failed: {e}")
    return None


def apply_halftone(img_path: str, w: int, h: int) -> Image.Image:
    img = Image.open(img_path).convert("L")
    iw, ih = img.size
    target_ratio = w / h
    current_ratio = iw / ih
    if current_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        left = (iw - new_w) // 2
        img = img.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        img = img.crop((0, 0, iw, new_h))
    img = img.resize((w, h), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.9)
    img = ImageEnhance.Brightness(img).enhance(0.85)
    halftone = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    return halftone.convert("RGB")


def draw_fallback_avatar(d: ImageDraw.ImageDraw, handle: str,
                         x: int, y: int, w: int, h: int):
    hv = _h(handle)
    shade = ((hv % 60) + 30, (hv % 50) + 40, (hv % 70) + 50)
    ix, iy, iw, ih = x + 8, y + 8, w - 16, h - 16
    d.rectangle([ix, iy, ix + iw, iy + ih], fill=shade)
    cx = ix + iw // 2
    hr = iw // 4
    cy = iy + ih * 28 // 100
    dark = tuple(max(0, c - 30) for c in shade)
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=dark)
    st = cy + hr
    d.polygon([(cx - iw // 3, iy + ih), (cx - hr + 5, st + 8),
               (cx + hr - 5, st + 8), (cx + iw // 3, iy + ih)], fill=dark)


# ── Radar Chart ─────────────────────────────────────────────────────
def draw_radar_chart(img: Image.Image, dims: list[dict],
                     cx: int, cy: int, radius: int):
    """Draw an 8-axis radar chart with filled polygon."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    n = len(dims)
    if n == 0:
        return

    angle_offset = -math.pi / 2

    def _pt(axis_idx: int, pct: float) -> tuple[int, int]:
        a = angle_offset + (2 * math.pi * axis_idx / n)
        return (int(cx + radius * pct * math.cos(a)),
                int(cy + radius * pct * math.sin(a)))

    # Grid rings at 25%, 50%, 75%, 100%
    for ring_pct in (0.25, 0.50, 0.75, 1.0):
        ring_pts = [_pt(i, ring_pct) for i in range(n)]
        ring_pts.append(ring_pts[0])
        od.line(ring_pts, fill=(200, 200, 200, 120), width=1)

    # Axis lines
    for i in range(n):
        od.line([_pt(i, 0), _pt(i, 1.0)], fill=(200, 200, 200, 120), width=1)

    # Data polygon (filled)
    data_pts = [_pt(i, dims[i]["score"] / 100.0) for i in range(n)]
    od.polygon(data_pts, fill=(43, 92, 230, 80), outline=(43, 92, 230, 240))
    od.line(data_pts + [data_pts[0]], fill=BLUE, width=2)

    # Data points
    for pt in data_pts:
        od.ellipse([pt[0] - 3, pt[1] - 3, pt[0] + 3, pt[1] + 3],
                   fill=BLUE, outline=WHITE)

    # Labels
    label_font = F(11, "semi")
    for i, dim in enumerate(dims):
        a = angle_offset + (2 * math.pi * i / n)
        lx = int(cx + (radius + 18) * math.cos(a))
        ly = int(cy + (radius + 18) * math.sin(a))
        short = dim["name"].replace("AI ", "").replace("Prompt ", "Prompt\n")
        bb = od.textbbox((0, 0), short, font=label_font)
        tw_ = bb[2] - bb[0]
        th_ = bb[3] - bb[1]
        # Anchor adjustment based on position
        if abs(math.cos(a)) < 0.3:
            lx -= tw_ // 2
        elif math.cos(a) < 0:
            lx -= tw_ + 2
        else:
            lx += 2
        if abs(math.sin(a)) < 0.3:
            ly -= th_ // 2
        elif math.sin(a) < 0:
            ly -= th_
        od.text((lx, ly), short, fill=(60, 60, 60, 255), font=label_font)

    img.paste(Image.alpha_composite(
        img.convert("RGBA"), overlay).convert("RGB"), (0, 0))


# ── Progress Bar ────────────────────────────────────────────────────
def draw_progress_bar(d: ImageDraw.ImageDraw, x: int, y: int,
                      w: int, h: int, pct: float):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=LGRAY)
    fill_w = max(h, int(w * pct))
    d.rounded_rectangle([x, y, x + fill_w, y + h], radius=h // 2, fill=BLUE)


# ── Barcode ─────────────────────────────────────────────────────────
def draw_barcode(d, handle, x, y, max_w, h):
    hv = _h(handle)
    cur = x
    drawing = True
    for idx in range(300):
        if cur >= x + max_w:
            break
        bits = (hv >> ((idx * 3) % 30)) & 0x7
        w = 1 + (bits % 3)
        if drawing:
            d.rectangle([int(cur), y, int(cur + w), y + h], fill=BLACK)
        cur += w
        drawing = not drawing
        if idx % 20 == 19:
            hv = _h(handle + str(idx))


# ── Main Card Generator ────────────────────────────────────────────
def generate(data: dict, out_path: str, avatar_path: str | None = None) -> str:
    handle = data["handle"]
    total = float(data["total_score"])

    level = data.get("level") or score_to_level(total)
    role = data.get("role") or score_to_role(total)
    summary = data.get("summary", "")

    img = Image.new("RGB", (IMG_W, IMG_H), BLUE)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H],
        radius=RADIUS, fill=WHITE,
    )

    lx = CARD_X + PAD
    rx = RIGHT_END

    # ── top bar ──
    d.text((lx, CARD_Y + 14), "loading / hermes id ai scorecard", fill=GRAY, font=F(11))
    t = "**Hermes ID"
    d.text((rx - tw(d, t, F(11, "semi")), CARD_Y + 14), t, fill=BLUE, font=F(11, "semi"))

    # ── avatar frame ──
    d.rectangle([AVATAR_X, AVATAR_Y, AVATAR_X + AVATAR_W, AVATAR_Y + AVATAR_H],
                outline=BLUE, width=3)
    d.rectangle([AVATAR_X + 5, AVATAR_Y + 5, AVATAR_X + AVATAR_W - 5, AVATAR_Y + AVATAR_H - 5],
                outline=BLUE, width=2)

    inner_x, inner_y = AVATAR_X + 8, AVATAR_Y + 8
    inner_w, inner_h = AVATAR_W - 16, AVATAR_H - 16

    real_avatar = avatar_path
    if not real_avatar or not os.path.exists(real_avatar):
        real_avatar = fetch_x_avatar(handle)

    if real_avatar and os.path.exists(real_avatar):
        av_img = apply_halftone(real_avatar, inner_w, inner_h)
        img.paste(av_img, (inner_x, inner_y))
    else:
        draw_fallback_avatar(d, handle, AVATAR_X, AVATAR_Y, AVATAR_W, AVATAR_H)

    # ── title (right of avatar) ──
    ry = AVATAR_Y - 2
    qf = F(32, "title")
    d.text((RIGHT_X - 4, ry - 6), "\u201C", fill=BLUE, font=qf)

    ry += 14
    tf = F(38, "title")
    for line in ("AI", "IDENTIFICATION", "CARD"):
        d.text((RIGHT_X, ry), line, fill=BLUE, font=tf)
        ry += 42
    last_w = tw(d, "CARD", tf)
    d.text((RIGHT_X + last_w + 4, ry - 36), "\u201D", fill=BLUE, font=qf)

    # ── info fields ──
    ry += 10
    fb = F(20, "bold")
    fv = F(22, "semi")
    fs = F(26, "bold")

    fields = [
        ("[name]", f"@{handle}", fv),
        ("[AI Score]", f"{total}/100", fs),
        ("[Level]", level, fv),
        ("[Role*]", role, fv),
    ]
    for label, val, vf in fields:
        d.text((RIGHT_X, ry), label, fill=BLACK, font=fb)
        vw = tw(d, val, vf)
        d.text((rx - vw, ry), val, fill=BLACK, font=vf)
        ry += 34

    # ── radar chart section ──
    radar_y = max(ry + 8, AVATAR_Y + AVATAR_H + 8)
    d.line([(lx, radar_y), (rx, radar_y)], fill=LGRAY, width=1)
    radar_y += 6

    all_dims = data.get("dimensions", [])
    # Ensure we have exactly 8 dims for the radar, pad if needed
    DIM_NAMES = ["AI Usage", "AI Understanding", "Communication", "Product Building",
                 "Adoption Speed", "Prompt Engineering", "Critical Awareness", "Knowledge Sharing"]
    dim_map = {d_["name"]: d_["score"] for d_ in all_dims}
    radar_dims = [{"name": n, "score": dim_map.get(n, 0)} for n in DIM_NAMES]

    radar_cx = CARD_X + CARD_W // 2
    radar_cy = radar_y + 115
    radar_r = 95

    draw_radar_chart(img, radar_dims, radar_cx, radar_cy, radar_r)
    d = ImageDraw.Draw(img)  # re-acquire after paste

    # ── proficiencies with progress bars (all 8) ──
    prof_y = radar_cy + radar_r + 32
    d.line([(lx, prof_y - 6), (rx, prof_y - 6)], fill=LGRAY, width=1)
    d.text((lx, prof_y), "[AI Proficiencies]", fill=BLACK, font=fb)
    prof_y += 30

    pf = F(14, "body")
    psf = F(14, "bold")
    bar_w = 200
    bar_h = 8

    sorted_dims = sorted(all_dims, key=lambda x: x["score"], reverse=True)
    for dim in sorted_dims[:8]:
        d.text((lx + 6, prof_y), dim["name"], fill=DARK, font=pf)
        bar_x = rx - bar_w - 40
        draw_progress_bar(d, bar_x, prof_y + 4, bar_w, bar_h, dim["score"] / 100.0)
        sc = str(dim["score"])
        d.text((rx - tw(d, sc, psf), prof_y), sc, fill=BLACK, font=psf)
        prof_y += 24

    # ── personalized summary ──
    prof_y += 10
    if summary:
        sf_font = F(13, "semi")
        qf_s = F(20, "title")
        max_tw_ = rx - lx - 40
        words = summary.split()
        lines = []
        cur_line = ""
        for w in words:
            test = f"{cur_line} {w}".strip()
            if tw(d, test, sf_font) <= max_tw_:
                cur_line = test
            else:
                if cur_line:
                    lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)

        d.text((lx + 6, prof_y - 4), "\u201C", fill=BLUE, font=qf_s)
        for ln in lines[:2]:
            cx_ = (lx + rx) // 2 - tw(d, ln, sf_font) // 2
            d.text((cx_, prof_y), ln, fill=DARK, font=sf_font)
            prof_y += 18
        last_line = lines[-1] if lines else ""
        last_cx = (lx + rx) // 2 - tw(d, last_line, sf_font) // 2
        d.text((last_cx + tw(d, last_line, sf_font) + 4, prof_y - 20), "\u201D", fill=BLUE, font=qf_s)

    # ── CTA ──
    prof_y += 12
    cta_font = F(12, "semi")
    cta = f"Tag @Hermes_ID and challenge your friends \u2014 test any @handle!"
    cta_w = tw(d, cta, cta_font)
    d.text(((lx + rx) // 2 - cta_w // 2, prof_y), cta, fill=BLUE, font=cta_font)

    # ── bottom ──
    by = CARD_Y + CARD_H - 78
    d.text((lx, by), "Hermes Agent", fill=BLUE, font=F(38, "cursive"))
    draw_barcode(d, handle, rx - 230, by + 6, 230, 32)

    d.line([(lx, by + 44), (rx, by + 44)], fill=LGRAY, width=1)
    sf = F(10)
    d.text((lx, by + 50), "Powered by Hermes Agent \u00b7 Test your AI Native level", fill=GRAY, font=sf)
    cr = "X @Hermes_ID"
    d.text((rx - tw(d, cr, sf), by + 50), cr, fill=GRAY, font=sf)

    # ── footer ──
    ff = F(22, "bold")
    ft = "hermesid.wtf"
    d.text(((IMG_W - tw(d, ft, ff)) // 2, CARD_Y + CARD_H + 18), ft, fill=WHITE, font=ff)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Card saved: {out_path}")

    share_url = build_share_url(handle, total, level)
    html_path = out_path.rsplit(".", 1)[0] + ".html"
    build_share_page(html_path, out_path, handle, total, level, role, summary)
    print(f"Share page: {html_path}")
    print(f"Share URL:  {share_url}")
    return out_path


def build_share_url(handle: str, score: float, level: str) -> str:
    import urllib.parse
    tweet = (
        f"My AI Score: {score}/100 \u2014 {level} \U0001f9e0\n\n"
        f"Just got my AI Identification Card from @Hermes_ID \U0001f4a1\n\n"
        f"Think you can beat me? Test yours \u2b07\ufe0f\n"
        f"hermesid.wtf"
    )
    return "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": tweet})


def build_share_page(html_path: str, img_path: str,
                     handle: str, score: float, level: str,
                     role: str, summary: str):
    """Generate an HTML page with the card + Share on X button."""
    import base64
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    share_url = build_share_url(handle, score, level)
    img_name = os.path.basename(img_path)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes ID \u2014 @{handle}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  min-height: 100vh;
  background: linear-gradient(135deg, #1a3af0 0%, #2b5ce6 50%, #4a7aff 100%);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  padding: 24px;
}}
.card-container {{ max-width: 420px; width: 100%; }}
.card-img {{
  width: 100%; border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  transition: transform 0.2s;
}}
.card-img:hover {{ transform: scale(1.02); }}
.actions {{
  display: flex; gap: 12px; margin-top: 20px; width: 100%;
}}
.btn {{
  flex: 1; padding: 16px 20px; border-radius: 12px;
  font-size: 16px; font-weight: 700; cursor: pointer;
  text-decoration: none; text-align: center;
  transition: all 0.2s; border: none;
}}
.btn-share {{
  background: #000; color: #fff;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}}
.btn-share:hover {{ background: #222; transform: translateY(-2px); }}
.btn-download {{
  background: rgba(255,255,255,0.15); color: #fff;
  backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3);
}}
.btn-download:hover {{ background: rgba(255,255,255,0.25); transform: translateY(-2px); }}
.x-logo {{ width: 18px; height: 18px; }}
.steps {{
  margin-top: 16px; padding: 16px 20px;
  background: rgba(255,255,255,0.1); border-radius: 12px;
  backdrop-filter: blur(10px); color: rgba(255,255,255,0.9);
  font-size: 13px; line-height: 1.6;
}}
.steps ol {{ padding-left: 18px; }}
.steps li {{ margin-bottom: 4px; }}
.footer {{
  margin-top: 24px; color: rgba(255,255,255,0.6);
  font-size: 12px; text-align: center;
}}
.footer a {{ color: rgba(255,255,255,0.8); }}
</style>
</head>
<body>
<div class="card-container">
  <img src="data:image/png;base64,{b64}" alt="Hermes ID Card @{handle}" class="card-img" id="cardImg">

  <div class="actions">
    <a href="{share_url}" target="_blank" rel="noopener" class="btn btn-share">
      <svg class="x-logo" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
      Share on X
    </a>
    <a href="data:image/png;base64,{b64}" download="{img_name}" class="btn btn-download">
      \u2b07 Download
    </a>
  </div>

  <div class="steps">
    <ol>
      <li>Click <strong>"Share on X"</strong> \u2014 tweet text is pre-filled</li>
      <li>Click the image icon in the tweet composer</li>
      <li>Attach your card image (already downloaded or save from above)</li>
      <li>Hit <strong>Post</strong> &#x1F680;</li>
    </ol>
  </div>

  <div class="footer">
    Powered by <a href="https://hermesid.wtf">Hermes Agent</a> &middot; @Hermes_ID
  </div>
</div>
</body>
</html>"""

    with open(html_path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_card.py <score.json> <output.png> [--avatar <path>]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    avatar = None
    if "--avatar" in sys.argv:
        idx = sys.argv.index("--avatar")
        if idx + 1 < len(sys.argv):
            avatar = sys.argv[idx + 1]

    generate(data, sys.argv[2], avatar_path=avatar)
