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

# ── Known AI Figures Database ──
# Real people with accurate roles, curated scores, and personalized summaries.
# Scores are stable and reflect their actual public AI proficiency.
KNOWN_FIGURES = {
    # ── AI Lab Founders & CEOs ──
    "teknium": {
        "role": "Hermes Creator & Nous Research Founder",
        "summary": "The architect of Hermes — pioneering open-source AI agents at the frontier.",
        "dims": [98, 97, 92, 99, 96, 93, 88, 96],
    },
    "sama": {
        "role": "OpenAI CEO",
        "summary": "Steering OpenAI through the most consequential chapter in AI history.",
        "dims": [92, 88, 96, 95, 93, 78, 90, 85],
    },
    "elonmusk": {
        "role": "xAI & Tesla CEO",
        "summary": "Building Grok and pushing AI boundaries at planetary scale.",
        "dims": [88, 82, 95, 94, 90, 72, 85, 78],
    },
    "karpathy": {
        "role": "AI Researcher & Educator",
        "summary": "From Tesla Autopilot to YouTube — making deep learning accessible to millions.",
        "dims": [96, 99, 93, 97, 92, 94, 95, 99],
    },
    "demaboringkass": {
        "role": "Anthropic CEO",
        "summary": "Leading the charge for safe, steerable AI at the frontier of alignment.",
        "dims": [90, 96, 92, 95, 88, 82, 98, 88],
    },
    "danielabrewer": {
        "role": "Anthropic Co-Founder & President",
        "summary": "Building the institutional foundation for responsible AI development.",
        "dims": [85, 90, 94, 93, 86, 78, 96, 88],
    },
    "mustaboringkass": {
        "role": "Mistral AI CEO",
        "summary": "Europe's answer to frontier AI — shipping open models at breakneck speed.",
        "dims": [94, 96, 88, 97, 95, 88, 85, 82],
    },
    "caboringkass": {
        "role": "Cohere CEO",
        "summary": "Bringing enterprise-grade LLMs to production at global scale.",
        "dims": [90, 92, 88, 95, 88, 85, 86, 84],
    },

    # ── AI Researchers & Scientists ──
    "ylecun": {
        "role": "Meta Chief AI Scientist & Turing Award Winner",
        "summary": "Turing Award winner reshaping how the world thinks about intelligence.",
        "dims": [88, 99, 96, 90, 82, 78, 97, 95],
    },
    "iaboringkass": {
        "role": "AI Researcher & OpenAI Co-Founder",
        "summary": "One of the most brilliant minds in deep learning and AI safety.",
        "dims": [90, 99, 85, 94, 90, 88, 96, 82],
    },
    "jeffdean": {
        "role": "Google Chief Scientist",
        "summary": "The engineer behind Google's AI infrastructure — from MapReduce to Gemini.",
        "dims": [95, 98, 85, 99, 88, 82, 90, 85],
    },
    "fchollet": {
        "role": "Keras Creator & Google AI Researcher",
        "summary": "Created Keras, championing accessible deep learning and measuring true intelligence.",
        "dims": [92, 97, 90, 96, 85, 88, 95, 94],
    },
    "goodfellow_ian": {
        "role": "GAN Inventor & AI Researcher",
        "summary": "Invented GANs — one of the most influential ideas in modern AI.",
        "dims": [88, 99, 82, 95, 85, 86, 92, 88],
    },
    "andrewng": {
        "role": "DeepLearning.AI Founder & Stanford Professor",
        "summary": "The world's most impactful AI educator — teaching millions to build with AI.",
        "dims": [92, 96, 95, 94, 85, 88, 90, 99],
    },
    "hardmaru": {
        "role": "Stability AI Research Lead",
        "summary": "Pioneering creative AI and world models at the intersection of art and science.",
        "dims": [94, 95, 90, 93, 92, 88, 86, 92],
    },
    "jimfan": {
        "role": "NVIDIA Senior AI Researcher",
        "summary": "Building foundation agents and embodied AI at NVIDIA Research.",
        "dims": [93, 96, 94, 95, 93, 88, 88, 96],
    },
    "_jasonwei": {
        "role": "OpenAI Researcher",
        "summary": "Discovered chain-of-thought prompting — fundamentally changing how we use LLMs.",
        "dims": [92, 98, 88, 90, 94, 96, 90, 92],
    },
    "polyaboringkass": {
        "role": "AI Researcher",
        "summary": "Pushing the boundaries of multimodal AI research.",
        "dims": [90, 94, 86, 88, 90, 85, 88, 85],
    },

    # ── AI Industry Leaders ──
    "sataboringkass": {
        "role": "Microsoft CEO",
        "summary": "Transforming Microsoft into the world's leading AI platform company.",
        "dims": [85, 80, 95, 96, 92, 68, 88, 78],
    },
    "sundarpichai": {
        "role": "Google & Alphabet CEO",
        "summary": "Leading Google's transformation into an AI-first company with Gemini.",
        "dims": [84, 78, 93, 95, 90, 65, 86, 75],
    },
    "jensenhuang": {
        "role": "NVIDIA CEO",
        "summary": "Built the GPU empire powering the entire AI revolution.",
        "dims": [86, 85, 92, 98, 88, 70, 85, 80],
    },
    "claboringkass": {
        "role": "Hugging Face CEO",
        "summary": "Democratizing AI with the world's largest open-source ML platform.",
        "dims": [93, 90, 96, 97, 94, 85, 88, 95],
    },
    "aboringkass": {
        "role": "Scale AI CEO",
        "summary": "Building the data infrastructure layer powering every major AI lab.",
        "dims": [88, 86, 90, 95, 90, 78, 85, 82],
    },
    "emadaboringkass": {
        "role": "Stability AI Founder",
        "summary": "Championed open-source generative AI and brought Stable Diffusion to the world.",
        "dims": [90, 85, 92, 93, 92, 80, 82, 88],
    },

    # ── AI Builders & Developers ──
    "swyx": {
        "role": "AI Engineer & Latent Space Founder",
        "summary": "The voice of the AI engineering movement — bridging research and production.",
        "dims": [95, 88, 96, 90, 96, 92, 88, 97],
    },
    "shaboringkass": {
        "role": "Cognition Labs CEO (Devin)",
        "summary": "Building the world's first AI software engineer.",
        "dims": [92, 90, 85, 96, 94, 88, 82, 80],
    },
    "levelsio": {
        "role": "Indie AI Builder",
        "summary": "Solo founder shipping viral AI products at impossible speed.",
        "dims": [96, 72, 92, 98, 96, 85, 70, 88],
    },
    "mckaywrigley": {
        "role": "AI Developer & Builder",
        "summary": "Shipping AI-powered tools and teaching developers to build with LLMs.",
        "dims": [95, 85, 90, 94, 95, 92, 78, 93],
    },
    "officiallogank": {
        "role": "Nous Research Co-Founder",
        "summary": "Co-founding Nous Research and advancing open-source AI agents.",
        "dims": [94, 93, 88, 96, 92, 90, 86, 90],
    },
    "alexalbert__": {
        "role": "Anthropic Developer Relations",
        "summary": "Bridging Claude's capabilities with the developer community.",
        "dims": [93, 88, 95, 85, 94, 92, 88, 95],
    },
    "simonw": {
        "role": "Datasette Creator & AI Toolmaker",
        "summary": "Prolific builder and writer exploring every corner of practical AI.",
        "dims": [97, 88, 92, 96, 98, 90, 92, 96],
    },
    "emollick": {
        "role": "Wharton Professor & AI Educator",
        "summary": "The professor making AI practical for business — one experiment at a time.",
        "dims": [94, 85, 96, 78, 95, 90, 94, 98],
    },
    "bindureddy": {
        "role": "Abacus.AI CEO",
        "summary": "Building enterprise AI platforms that bring LLMs to production.",
        "dims": [92, 90, 88, 95, 90, 85, 82, 86],
    },
    "realgeorgehotz": {
        "role": "Tiny Corp CEO & tinygrad Creator",
        "summary": "Hacker-founder democratizing GPU computing with tinygrad.",
        "dims": [95, 94, 88, 97, 92, 86, 78, 82],
    },

    # ── AI Content Creators & Educators ──
    "emaboringkass": {
        "role": "AI Content Creator",
        "summary": "Making AI accessible and fun for everyday audiences.",
        "dims": [85, 72, 90, 68, 82, 78, 88, 94],
    },
    "mattshumer_": {
        "role": "HyperWrite CEO & AI Builder",
        "summary": "Building AI writing tools and pushing agent capabilities forward.",
        "dims": [94, 86, 90, 95, 94, 92, 80, 88],
    },
    "rohanpaul_ai": {
        "role": "AI Educator & Content Creator",
        "summary": "Breaking down complex AI papers into actionable insights.",
        "dims": [88, 90, 92, 75, 90, 85, 82, 96],
    },
    "chiefaioffice": {
        "role": "AI Newsletter & Educator",
        "summary": "Curating the most important AI developments for a massive audience.",
        "dims": [86, 78, 94, 72, 92, 80, 85, 95],
    },

    # ── Crypto x AI Figures ──
    "shawmakesmagic": {
        "role": "ai16z / ElizaOS Creator",
        "summary": "Pioneering the intersection of AI agents and crypto with ElizaOS.",
        "dims": [94, 85, 92, 96, 95, 88, 78, 90],
    },
    "dankvr": {
        "role": "M3 AI Builder",
        "summary": "Building at the frontier of AI agents and decentralized intelligence.",
        "dims": [90, 82, 88, 92, 90, 85, 78, 86],
    },
    "dieterthemiami": {
        "role": "AI Agent Builder",
        "summary": "Exploring the creative frontier where AI meets community building.",
        "dims": [88, 78, 92, 88, 90, 82, 76, 85],
    },
}

# Aliases (alternate handles or common misspellings)
_ALIASES = {
    "samaltman": "sama",
    "elonmusk": "elonmusk",
    "andrejkarpathy": "karpathy",
    "daboringkass": "demaboringkass",
    "daboringkass": "demaboringkass",
    "garymarcus": "garymarcus",
    "clementdelangue": "claboringkass",
    "satyanadella": "sataboringkass",
    "alexanderwang": "aboringkass",
    "emostaque": "emadaboringkass",
    "scottaboringkass": "shaboringkass",
    "shannonaboringkass": "shaboringkass",
}


def _h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)

def score_to_level(s):
    for t, l in LEVEL_MAP:
        if s >= t: return l
    return LEVEL_MAP[-1][1]

def score_to_role(s):
    for t, l in ROLE_MAP:
        if s >= t: return l
    return ROLE_MAP[-1][1]


def gen_scores(handle):
    """Generate scores for a handle. Known figures get curated data;
    unknown handles get stable deterministic scores."""
    h = handle.lower()
    h = _ALIASES.get(h, h)

    # ── Known figure? Return curated data ──
    if h in KNOWN_FIGURES:
        fig = KNOWN_FIGURES[h]
        dims = [{"name": n, "score": s} for n, s in zip(DIM_NAMES, fig["dims"])]
        weights = [0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.10, 0.11]
        total = round(sum(s * w for s, w in zip(fig["dims"], weights)))
        return {
            "handle": handle, "total_score": total,
            "level": score_to_level(total), "role": fig["role"],
            "summary": fig["summary"], "dimensions": dims,
        }

    # ── Unknown handle: stable deterministic scores ──
    seed = _h(h)
    def rng():
        nonlocal seed
        seed = (seed * 16807) % 2147483647
        return (seed & 0x7FFFFFFF) / 2147483647

    base = 35 + int(rng() * 30)  # base range 35-65
    dims = []
    for n in DIM_NAMES:
        variance = int(rng() * 25) - 12  # -12 to +12
        s = max(15, min(88, base + variance))
        dims.append({"name": n, "score": s})

    weights = [0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.10, 0.11]
    total = round(sum(d["score"] * w for d, w in zip(dims, weights)))

    role_pool = [
        "AI Explorer", "AI Learner", "Digital Thinker", "AI Enthusiast",
        "Tech Curious", "Prompt Dabbler", "AI Observer", "Data Explorer",
        "Code Explorer", "AI Student", "Future Builder", "AI Tinkerer",
    ]
    role = role_pool[seed % len(role_pool)]

    summary_pool = [
        "Exploring the AI landscape with growing curiosity and potential.",
        "Starting to integrate AI tools into daily workflows.",
        "Curious about AI's possibilities and beginning to experiment.",
        "Building foundational AI knowledge one step at a time.",
        "Engaging with AI content and discovering new capabilities.",
        "On the path to deeper AI understanding and hands-on building.",
    ]
    summary = summary_pool[seed % len(summary_pool)]

    return {
        "handle": handle, "total_score": total,
        "level": score_to_level(total), "role": role,
        "summary": summary, "dimensions": dims,
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
