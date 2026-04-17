#!/usr/bin/env python3
"""
Hermes ID — Card Generation API
Runs on VPS alongside nginx. Generates real PNG cards on-the-fly.
"""

from __future__ import annotations

import json, math, os, sys, hashlib, io, urllib.request, urllib.parse
from pathlib import Path

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
except ImportError:
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

app = Flask(__name__)
CORS(app)

CACHE_DIR = Path("/tmp/hermes-cards")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_CACHE = Path("/tmp/hermes-avatars")
AVATAR_CACHE.mkdir(parents=True, exist_ok=True)

# ── Colors ──
BLUE = (43, 92, 230)
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
DARK = (51, 51, 51)
GRAY = (136, 136, 136)
LGRAY = (225, 225, 225)

# ── Layout ──
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

LEVEL_MAP = [
    (95, "Agent God"), (88, "AI Native"), (78, "AI Strategist"),
    (65, "AI Explorer"), (50, "AI Curious"), (35, "AI Aware"), (0, "AI Normie"),
]
ROLE_MAP = [
    (95, "Hermes Creator"), (88, "AI Innovator"), (78, "AI Architect"),
    (65, "AI Practitioner"), (50, "AI Learner"), (0, "AI Observer"),
]

DIM_NAMES = [
    "AI Usage", "AI Understanding", "Communication", "Product Building",
    "Adoption Speed", "Prompt Engineering", "Critical Awareness", "Knowledge Sharing",
]
SUMMARIES = [
    "A relentless builder who lives at the bleeding edge of AI innovation.",
    "Deeply embedded in the AI ecosystem with strong technical intuition.",
    "Strategic thinker who understands AI's potential and applies it wisely.",
    "Actively exploring AI tools and growing skills every day.",
    "Curious mind just beginning to discover the power of AI.",
    "Early in the AI journey with great potential ahead.",
]


def _h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)

def score_to_level(s):
    for t, l in LEVEL_MAP:
        if s >= t: return l
    return LEVEL_MAP[-1][1]

def score_to_role(s):
    for t, l in ROLE_MAP:
        if s >= t: return l
    return ROLE_MAP[-1][1]

def get_summary(s):
    if s >= 90: return SUMMARIES[0]
    if s >= 80: return SUMMARIES[1]
    if s >= 70: return SUMMARIES[2]
    if s >= 55: return SUMMARIES[3]
    if s >= 35: return SUMMARIES[4]
    return SUMMARIES[5]

def gen_scores(handle):
    seed = _h(handle.lower())
    def rng():
        nonlocal seed
        seed = (seed * 16807) % 2147483647
        return (seed & 0x7FFFFFFF) / 2147483647
    dims = [{"name": n, "score": int(40 + rng() * 55)} for n in DIM_NAMES]
    total = round(sum(d["score"] for d in dims) / len(dims))
    return {
        "handle": handle, "total_score": total,
        "level": score_to_level(total), "role": score_to_role(total),
        "summary": get_summary(total), "dimensions": dims,
    }


# ── Font Management ──
FONT_DIR = Path("/tmp/hermes-fonts")
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
_fc = {}

def _dl(fname):
    dest = FONT_DIR / fname
    if dest.exists(): return str(dest)
    url = FONT_URLS.get(fname)
    if not url: return None
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(dest))
        return str(dest)
    except: return None

def _sf(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except: continue
    return ImageFont.load_default(size=sz)

_STYLES = {
    "title": "PermanentMarker-Regular.ttf", "cursive": "Caveat-Bold.ttf",
    "body": "Inter_18pt-Regular.ttf", "bold": "Inter_18pt-Bold.ttf",
    "semi": "Inter_18pt-SemiBold.ttf",
}

def F(sz, style="body"):
    k = f"{style}:{sz}"
    if k in _fc: return _fc[k]
    p = _dl(_STYLES.get(style, _STYLES["body"]))
    if p:
        try:
            f = ImageFont.truetype(p, sz); _fc[k] = f; return f
        except: pass
    f = _sf(sz); _fc[k] = f; return f

def tw(d, txt, f):
    bb = d.textbbox((0, 0), txt, font=f); return bb[2] - bb[0]

def th(d, txt, f):
    bb = d.textbbox((0, 0), txt, font=f); return bb[3] - bb[1]


# ── Avatar ──
def fetch_avatar(handle):
    cached = AVATAR_CACHE / f"{handle.lower()}.jpg"
    if cached.exists() and cached.stat().st_size > 1000:
        return str(cached)
    url = f"https://unavatar.io/x/{handle}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesID/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        if len(data) > 500:
            cached.write_bytes(data)
            return str(cached)
    except: pass
    return None

def apply_halftone(img_path, w, h):
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

def draw_fallback_avatar(d, handle, x, y, w, h):
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


# ── Radar Chart ──
def draw_radar_chart(img, dims, cx, cy, radius):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    n = len(dims)
    if n == 0: return
    angle_offset = -math.pi / 2

    def _pt(i, pct):
        a = angle_offset + (2 * math.pi * i / n)
        return (int(cx + radius * pct * math.cos(a)),
                int(cy + radius * pct * math.sin(a)))

    for ring_pct in (0.25, 0.50, 0.75, 1.0):
        pts = [_pt(i, ring_pct) for i in range(n)] + [_pt(0, ring_pct)]
        od.line(pts, fill=(200, 200, 200, 120), width=1)
    for i in range(n):
        od.line([_pt(i, 0), _pt(i, 1.0)], fill=(200, 200, 200, 120), width=1)

    data_pts = [_pt(i, dims[i]["score"] / 100.0) for i in range(n)]
    od.polygon(data_pts, fill=(43, 92, 230, 80), outline=(43, 92, 230, 240))
    od.line(data_pts + [data_pts[0]], fill=BLUE, width=2)
    for pt in data_pts:
        od.ellipse([pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3], fill=BLUE, outline=WHITE)

    label_font = F(11, "semi")
    for i, dim in enumerate(dims):
        a = angle_offset + (2 * math.pi * i / n)
        lx = int(cx + (radius + 18) * math.cos(a))
        ly = int(cy + (radius + 18) * math.sin(a))
        short = dim["name"].replace("AI ", "").replace("Prompt ", "Prompt\n")
        bb = od.textbbox((0, 0), short, font=label_font)
        tw_ = bb[2] - bb[0]; th_ = bb[3] - bb[1]
        if abs(math.cos(a)) < 0.3: lx -= tw_ // 2
        elif math.cos(a) < 0: lx -= tw_ + 2
        else: lx += 2
        if abs(math.sin(a)) < 0.3: ly -= th_ // 2
        elif math.sin(a) < 0: ly -= th_
        od.text((lx, ly), short, fill=(60, 60, 60, 255), font=label_font)

    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))


def draw_progress_bar(d, x, y, w, h, pct):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=LGRAY)
    fill_w = max(h, int(w * pct))
    d.rounded_rectangle([x, y, x + fill_w, y + h], radius=h // 2, fill=BLUE)

def draw_barcode(d, handle, x, y, max_w, h):
    hv = _h(handle)
    cur = x; drawing = True
    for idx in range(300):
        if cur >= x + max_w: break
        bits = (hv >> ((idx * 3) % 30)) & 0x7
        w = 1 + (bits % 3)
        if drawing:
            d.rectangle([int(cur), y, int(cur + w), y + h], fill=BLACK)
        cur += w; drawing = not drawing
        if idx % 20 == 19: hv = _h(handle + str(idx))


# ── Main Card Generator ──
def generate_card(data):
    handle = data["handle"]
    total = float(data["total_score"])
    level = data.get("level") or score_to_level(total)
    role = data.get("role") or score_to_role(total)
    summary = data.get("summary", "")

    img = Image.new("RGB", (IMG_W, IMG_H), BLUE)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        [CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H],
        radius=RADIUS, fill=WHITE)

    lx = CARD_X + PAD; rx = RIGHT_END

    # top bar
    d.text((lx, CARD_Y + 12), "loading / hermes id ai scorecard", fill=GRAY, font=F(14))
    t = "@Hermes_ID"
    d.text((rx - tw(d, t, F(14, "semi")), CARD_Y + 12), t, fill=BLUE, font=F(14, "semi"))

    # avatar frame
    d.rectangle([AVATAR_X, AVATAR_Y, AVATAR_X + AVATAR_W, AVATAR_Y + AVATAR_H], outline=BLUE, width=3)
    d.rectangle([AVATAR_X + 5, AVATAR_Y + 5, AVATAR_X + AVATAR_W - 5, AVATAR_Y + AVATAR_H - 5], outline=BLUE, width=2)
    inner_x, inner_y = AVATAR_X + 8, AVATAR_Y + 8
    inner_w, inner_h = AVATAR_W - 16, AVATAR_H - 16

    real_avatar = fetch_avatar(handle)
    if real_avatar and os.path.exists(real_avatar):
        av_img = apply_halftone(real_avatar, inner_w, inner_h)
        img.paste(av_img, (inner_x, inner_y))
    else:
        draw_fallback_avatar(d, handle, AVATAR_X, AVATAR_Y, AVATAR_W, AVATAR_H)

    # title
    ry = AVATAR_Y - 2
    qf = F(32, "title")
    d.text((RIGHT_X - 4, ry - 6), "\u201C", fill=BLUE, font=qf)
    ry += 14; tf = F(38, "title")
    for line in ("AI", "IDENTIFICATION", "CARD"):
        d.text((RIGHT_X, ry), line, fill=BLUE, font=tf); ry += 42
    last_w = tw(d, "CARD", tf)
    d.text((RIGHT_X + last_w + 4, ry - 36), "\u201D", fill=BLUE, font=qf)

    # info fields
    ry += 10; fb = F(20, "bold"); fv = F(22, "semi"); fs = F(26, "bold")
    fields = [("[name]", f"@{handle}", fv), ("[AI Score]", f"{total}/100", fs),
              ("[Level]", level, fv), ("[Role*]", role, fv)]
    for label, val, vf in fields:
        d.text((RIGHT_X, ry), label, fill=BLACK, font=fb)
        d.text((rx - tw(d, val, vf), ry), val, fill=BLACK, font=vf)
        ry += 34

    # radar chart
    radar_y = max(ry + 8, AVATAR_Y + AVATAR_H + 8)
    d.line([(lx, radar_y), (rx, radar_y)], fill=LGRAY, width=1)
    radar_y += 6
    all_dims = data.get("dimensions", [])
    dim_map = {d_["name"]: d_["score"] for d_ in all_dims}
    radar_dims = [{"name": n, "score": dim_map.get(n, 0)} for n in DIM_NAMES]
    radar_cx = CARD_X + CARD_W // 2; radar_cy = radar_y + 115; radar_r = 95
    draw_radar_chart(img, radar_dims, radar_cx, radar_cy, radar_r)
    d = ImageDraw.Draw(img)

    # proficiencies
    prof_y = radar_cy + radar_r + 32
    d.line([(lx, prof_y - 6), (rx, prof_y - 6)], fill=LGRAY, width=1)
    d.text((lx, prof_y), "[AI Proficiencies]", fill=BLACK, font=fb)
    prof_y += 30
    pf = F(14, "body"); psf = F(14, "bold"); bar_w = 200; bar_h = 8
    sorted_dims = sorted(all_dims, key=lambda x: x["score"], reverse=True)
    for dim in sorted_dims[:8]:
        d.text((lx + 6, prof_y), dim["name"], fill=DARK, font=pf)
        bar_x = rx - bar_w - 40
        draw_progress_bar(d, bar_x, prof_y + 4, bar_w, bar_h, dim["score"] / 100.0)
        sc = str(dim["score"]); d.text((rx - tw(d, sc, psf), prof_y), sc, fill=BLACK, font=psf)
        prof_y += 24

    # summary
    prof_y += 10
    if summary:
        sf_font = F(13, "semi"); qf_s = F(20, "title")
        max_tw_ = rx - lx - 40
        words = summary.split(); lines = []; cur_line = ""
        for w in words:
            test = f"{cur_line} {w}".strip()
            if tw(d, test, sf_font) <= max_tw_: cur_line = test
            else:
                if cur_line: lines.append(cur_line)
                cur_line = w
        if cur_line: lines.append(cur_line)
        d.text((lx + 6, prof_y - 4), "\u201C", fill=BLUE, font=qf_s)
        for ln in lines[:2]:
            cx_ = (lx + rx) // 2 - tw(d, ln, sf_font) // 2
            d.text((cx_, prof_y), ln, fill=DARK, font=sf_font); prof_y += 18
        if lines:
            last_line = lines[-1]
            last_cx = (lx + rx) // 2 - tw(d, last_line, sf_font) // 2
            d.text((last_cx + tw(d, last_line, sf_font) + 4, prof_y - 20), "\u201D", fill=BLUE, font=qf_s)

    # CTA
    prof_y += 12
    cta_font = F(12, "semi")
    cta = "Tag @Hermes_ID and challenge your friends \u2014 test any @handle!"
    cta_w = tw(d, cta, cta_font)
    d.text(((lx + rx) // 2 - cta_w // 2, prof_y), cta, fill=BLUE, font=cta_font)

    # bottom
    by = CARD_Y + CARD_H - 78
    d.text((lx, by), "Hermes Agent", fill=BLUE, font=F(38, "cursive"))
    draw_barcode(d, handle, rx - 230, by + 6, 230, 32)
    d.line([(lx, by + 44), (rx, by + 44)], fill=LGRAY, width=1)
    sf = F(10)
    d.text((lx, by + 50), "Powered by Hermes Agent \u00b7 Test your AI Native level", fill=GRAY, font=sf)
    cr = "X @Hermes_ID"
    d.text((rx - tw(d, cr, sf), by + 50), cr, fill=GRAY, font=sf)

    # footer
    ff = F(22, "bold"); ft = "hermesid.wtf"
    d.text(((IMG_W - tw(d, ft, ff)) // 2, CARD_Y + CARD_H + 18), ft, fill=WHITE, font=ff)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


@app.route("/api/card")
def api_card():
    handle = request.args.get("handle", "").strip().lstrip("@")
    if not handle or len(handle) > 30:
        return jsonify({"error": "Invalid handle"}), 400

    cache_path = CACHE_DIR / f"{handle.lower()}.png"
    if cache_path.exists():
        return send_file(str(cache_path), mimetype="image/png")

    data = gen_scores(handle)
    buf = generate_card(data)

    cache_path.write_bytes(buf.getvalue())
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/card/<handle>")
def card_page(handle):
    """HTML page with Twitter Card meta tags so the card image shows in tweets."""
    handle = handle.strip().lstrip("@")[:30]
    if not handle:
        return "Not found", 404

    cache_path = CACHE_DIR / f"{handle.lower()}.png"
    if not cache_path.exists():
        data = gen_scores(handle)
        buf = generate_card(data)
        cache_path.write_bytes(buf.getvalue())

    data = gen_scores(handle)
    score = data["total_score"]
    level = data["level"]

    card_img_url = f"https://hermesid.wtf/api/card?handle={handle}"
    page_url = f"https://hermesid.wtf/card/{handle}"

    tweet_text = (
        f"My AI Score: {score}/100 \u2014 {level} \U0001f9e0\n\n"
        f"Just got my AI Identification Card from @Hermes_ID \U0001f4a1\n\n"
        f"Think you can beat me? Test yours \u2b07\ufe0f\n"
        f"{page_url}"
    )
    share_href = "https://twitter.com/intent/tweet?text=" + urllib.parse.quote(tweet_text)

    html = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>@%(handle)s — AI Score %(score)s/100 | Hermes ID</title>
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Hermes_ID">
<meta name="twitter:title" content="@%(handle)s — %(level)s (%(score)s/100)">
<meta name="twitter:description" content="AI Identification Card — Test your AI native level at hermesid.wtf">
<meta name="twitter:image" content="%(card_img_url)s">
<meta property="og:type" content="website">
<meta property="og:url" content="%(page_url)s">
<meta property="og:title" content="@%(handle)s — %(level)s (%(score)s/100)">
<meta property="og:description" content="AI Identification Card — Test your AI native level at hermesid.wtf">
<meta property="og:image" content="%(card_img_url)s">
<meta property="og:image:width" content="640">
<meta property="og:image:height" content="1060">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;background:linear-gradient(135deg,#1a3af0,#2b5ce6 50%%,#4a7aff);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:-apple-system,sans-serif;padding:24px}
.wrap{max-width:420px;width:100%%;text-align:center}
img{width:100%%;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
.btns{display:flex;gap:12px;margin-top:20px}
.btn{flex:1;padding:16px;border-radius:12px;font-size:15px;font-weight:700;cursor:pointer;text-decoration:none;text-align:center;border:none;display:flex;align-items:center;justify-content:center;gap:8px;transition:all 0.2s}
.btn-share{background:#000;color:#fff}.btn-share:hover{background:#222;transform:translateY(-2px)}
.btn-get{background:rgba(255,255,255,0.15);color:#fff;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.3)}.btn-get:hover{background:rgba(255,255,255,0.25);transform:translateY(-2px)}
.foot{margin-top:20px;color:rgba(255,255,255,0.6);font-size:12px}.foot a{color:rgba(255,255,255,0.8)}
svg{width:18px;height:18px}
</style></head><body>
<div class="wrap">
<img src="%(card_img_url)s" alt="@%(handle)s AI ID Card">
<div class="btns">
<a href="%(share_href)s" target="_blank" class="btn btn-share"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>Share on X</a>
<a href="https://hermesid.wtf" class="btn btn-get">Get Your Card</a>
</div>
<p class="foot">Powered by <a href="https://hermesid.wtf">Hermes Agent</a> &middot; @Hermes_ID</p>
</div></body></html>""" % {
        "handle": handle, "score": score, "level": level,
        "card_img_url": card_img_url, "page_url": page_url,
        "share_href": share_href,
    }
    return html, 200, {"Content-Type": "text/html"}


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
