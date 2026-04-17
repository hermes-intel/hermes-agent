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
BIO_CACHE = Path("/tmp/hermes-bio-cache")
BIO_CACHE.mkdir(parents=True, exist_ok=True)

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

# ── Known Figures Database ──
# Real X handles with accurate roles, curated scores, and personalized summaries.
# dims order: [AI Usage, AI Understanding, Communication, Product Building,
#              Adoption Speed, Prompt Engineering, Critical Awareness, Knowledge Sharing]
KNOWN_FIGURES = {
    # ════════════════════════════════════════
    #  AI Lab Founders & CEOs
    # ════════════════════════════════════════
    "teknium": {"role": "Nous Research Founder",
        "summary": "The architect of Hermes — pioneering open-source AI agents at the frontier.",
        "dims": [98, 97, 92, 99, 96, 93, 88, 96]},
    "sama": {"role": "OpenAI CEO",
        "summary": "Steering OpenAI through the most consequential chapter in AI history.",
        "dims": [92, 88, 96, 95, 93, 78, 90, 85]},
    "elonmusk": {"role": "xAI & Tesla CEO",
        "summary": "Building Grok and pushing AI boundaries at planetary scale.",
        "dims": [88, 82, 95, 94, 90, 72, 85, 78]},
    "karpathy": {"role": "AI Researcher",
        "summary": "From Tesla Autopilot to YouTube — making deep learning accessible to millions.",
        "dims": [96, 99, 93, 97, 92, 94, 95, 99]},
    "daboringkass": {"role": "Anthropic CEO",
        "summary": "Leading the charge for safe, steerable AI at the frontier of alignment.",
        "dims": [90, 96, 92, 95, 88, 82, 98, 88]},
    "daboringkassei": {"role": "Anthropic President",
        "summary": "Building the institutional foundation for responsible AI development.",
        "dims": [85, 90, 94, 93, 86, 78, 96, 88]},
    "arthurmensch": {"role": "Mistral AI CEO",
        "summary": "Europe's answer to frontier AI — shipping open models at breakneck speed.",
        "dims": [94, 96, 88, 97, 95, 88, 85, 82]},
    "aidangomez": {"role": "Cohere CEO",
        "summary": "Bringing enterprise-grade LLMs to production at global scale.",
        "dims": [90, 94, 88, 95, 88, 85, 86, 84]},
    "officiallogank": {"role": "Nous Research Co-Founder",
        "summary": "Co-founding Nous Research and advancing open-source AI agents.",
        "dims": [94, 93, 88, 96, 92, 90, 86, 90]},

    # ════════════════════════════════════════
    #  AI Researchers & Scientists
    # ════════════════════════════════════════
    "ylecun": {"role": "Meta Chief AI Scientist",
        "summary": "Turing Award winner reshaping how the world thinks about intelligence.",
        "dims": [88, 99, 96, 90, 82, 78, 97, 95]},
    "ilyasut": {"role": "SSI Co-Founder",
        "summary": "One of the most brilliant minds in deep learning and AI safety.",
        "dims": [90, 99, 85, 94, 90, 88, 96, 82]},
    "jeffdean": {"role": "Google Chief Scientist",
        "summary": "The engineer behind Google's AI infrastructure — from MapReduce to Gemini.",
        "dims": [95, 98, 85, 99, 88, 82, 90, 85]},
    "fchollet": {"role": "Keras Creator",
        "summary": "Created Keras, championing accessible deep learning and measuring true intelligence.",
        "dims": [92, 97, 90, 96, 85, 88, 95, 94]},
    "goodfellow_ian": {"role": "GAN Inventor",
        "summary": "Invented GANs — one of the most influential ideas in modern AI.",
        "dims": [88, 99, 82, 95, 85, 86, 92, 88]},
    "andrewng": {"role": "DeepLearning.AI Founder",
        "summary": "The world's most impactful AI educator — teaching millions to build with AI.",
        "dims": [92, 96, 95, 94, 85, 88, 90, 99]},
    "hardmaru": {"role": "Stability AI Research",
        "summary": "Pioneering creative AI and world models at the intersection of art and science.",
        "dims": [94, 95, 90, 93, 92, 88, 86, 92]},
    "jimfan": {"role": "NVIDIA AI Researcher",
        "summary": "Building foundation agents and embodied AI at NVIDIA Research.",
        "dims": [93, 96, 94, 95, 93, 88, 88, 96]},
    "_jasonwei": {"role": "OpenAI Researcher",
        "summary": "Discovered chain-of-thought prompting — fundamentally changing how we use LLMs.",
        "dims": [92, 98, 88, 90, 94, 96, 90, 92]},
    "demaboringkass": {"role": "Google DeepMind CEO",
        "summary": "Merging DeepMind and Google Brain to build the most capable AI systems.",
        "dims": [88, 96, 90, 95, 86, 78, 92, 85]},
    "kaifulee": {"role": "Sinovation Ventures CEO",
        "summary": "Bridging AI between East and West — from Google China to bestselling AI author.",
        "dims": [90, 92, 95, 90, 85, 78, 92, 96]},
    "garymarcus": {"role": "NYU Professor",
        "summary": "The most vocal scientific critic of deep learning hype — demanding rigor.",
        "dims": [78, 92, 95, 72, 80, 68, 98, 92]},

    # ════════════════════════════════════════
    #  Tech Industry CEOs
    # ════════════════════════════════════════
    "satyanadella": {"role": "Microsoft CEO",
        "summary": "Transforming Microsoft into the world's leading AI platform company.",
        "dims": [85, 80, 95, 96, 92, 68, 88, 78]},
    "sundarpichai": {"role": "Google CEO",
        "summary": "Leading Google's transformation into an AI-first company with Gemini.",
        "dims": [84, 78, 93, 95, 90, 65, 86, 75]},
    "tim_cook": {"role": "Apple CEO",
        "summary": "Integrating Apple Intelligence across the world's most popular devices.",
        "dims": [78, 70, 90, 94, 82, 58, 85, 72]},
    "faboringkass": {"role": "Meta CEO",
        "summary": "Open-sourcing Llama and betting Meta's future on AI and the metaverse.",
        "dims": [86, 82, 88, 96, 90, 72, 80, 78]},
    "alexalbert__": {"role": "Anthropic DevRel",
        "summary": "Bridging Claude's capabilities with the developer community.",
        "dims": [93, 88, 95, 85, 94, 92, 88, 95]},

    # ════════════════════════════════════════
    #  VCs & Tech Investors
    # ════════════════════════════════════════
    "pmarca": {"role": "a16z Co-Founder",
        "summary": "The VC who bet biggest on AI — reshaping Silicon Valley's investment thesis.",
        "dims": [88, 82, 96, 90, 92, 72, 90, 88]},
    "paulg": {"role": "Y Combinator Founder",
        "summary": "The godfather of startup culture who saw AI's potential before most VCs.",
        "dims": [82, 78, 96, 88, 85, 80, 92, 95]},
    "naval": {"role": "AngelList Founder",
        "summary": "Philosopher-investor at the intersection of AI, wealth, and human potential.",
        "dims": [85, 78, 96, 85, 88, 75, 92, 94]},
    "balajis": {"role": "Tech Philosopher",
        "summary": "Prolific tech thinker connecting AI, crypto, and the future of nation-states.",
        "dims": [88, 85, 95, 88, 92, 78, 90, 92]},
    "peterthiel": {"role": "Founders Fund Partner",
        "summary": "Contrarian investor who funded the companies defining the AI era.",
        "dims": [78, 80, 88, 92, 82, 65, 90, 78]},
    "reidhoffman": {"role": "LinkedIn Co-Founder",
        "summary": "From LinkedIn to investing in OpenAI — always at the frontier of tech.",
        "dims": [86, 80, 94, 90, 88, 72, 88, 90]},
    "jason": {"role": "Angel Investor",
        "summary": "Silicon Valley's most prolific angel investor and AI startup evangelist.",
        "dims": [90, 75, 96, 88, 94, 80, 78, 92]},
    "cdixon": {"role": "a16z Crypto Partner",
        "summary": "Leading a16z's crypto fund at the convergence of blockchain and AI.",
        "dims": [85, 82, 90, 88, 86, 72, 88, 90]},

    # ════════════════════════════════════════
    #  Crypto Founders & Leaders
    # ════════════════════════════════════════
    "cz_binance": {"role": "Binance Founder",
        "summary": "Built the world's largest crypto exchange from zero to global dominance.",
        "dims": [82, 75, 95, 98, 90, 65, 78, 82]},
    "vitalikbuterin": {"role": "Ethereum Co-Founder",
        "summary": "The mind behind Ethereum — redefining decentralized computing for a generation.",
        "dims": [88, 98, 92, 96, 88, 82, 95, 94]},
    "brian_armstrong": {"role": "Coinbase CEO",
        "summary": "Building the most trusted bridge between traditional finance and crypto.",
        "dims": [82, 78, 90, 96, 88, 68, 85, 80]},
    "saylor": {"role": "MicroStrategy Chairman",
        "summary": "The most aggressive corporate Bitcoin buyer in history.",
        "dims": [78, 72, 95, 90, 82, 60, 75, 88]},
    "tyler": {"role": "Gemini Co-Founder",
        "summary": "From Facebook lawsuit to crypto exchange — building Gemini for the long term.",
        "dims": [80, 74, 88, 90, 84, 62, 80, 78]},
    "cameron": {"role": "Gemini Co-Founder",
        "summary": "Co-building Gemini and championing Bitcoin as digital gold.",
        "dims": [80, 74, 88, 90, 84, 62, 80, 78]},
    "aantonop": {"role": "Bitcoin Educator",
        "summary": "Mastering Bitcoin — the most influential crypto educator of all time.",
        "dims": [82, 90, 96, 78, 82, 72, 92, 99]},
    "staboringkass": {"role": "Aave Founder",
        "summary": "Pioneering DeFi lending and decentralized social with Lens Protocol.",
        "dims": [86, 88, 90, 96, 90, 78, 82, 85]},
    "jessepollak": {"role": "Base Creator",
        "summary": "Building Base — bringing the next billion users onchain.",
        "dims": [85, 82, 92, 95, 90, 75, 82, 88]},
    "rajgokal": {"role": "Solana Co-Founder",
        "summary": "Co-founding Solana and scaling blockchain to millions of transactions.",
        "dims": [84, 86, 88, 96, 88, 72, 80, 82]},
    "aaboringkass": {"role": "Solana CEO",
        "summary": "Building Solana into the fastest blockchain ecosystem in the world.",
        "dims": [86, 88, 88, 97, 90, 74, 82, 80]},
    "haaboringkass": {"role": "BitMEX Co-Founder",
        "summary": "Crypto's most provocative macro writer — essential reading for any trader.",
        "dims": [82, 85, 94, 88, 86, 70, 88, 92]},
    "cobie": {"role": "Crypto Investor",
        "summary": "One of crypto's sharpest minds — cutting through noise with data and wit.",
        "dims": [80, 78, 95, 82, 88, 68, 90, 85]},
    "blknoiz06": {"role": "Crypto Trader",
        "summary": "One of crypto Twitter's most followed traders — calling moves before they happen.",
        "dims": [82, 75, 94, 78, 90, 65, 80, 82]},
    "pentosh1": {"role": "Crypto Analyst",
        "summary": "Technical analysis meets crypto conviction — consistently ahead of the market.",
        "dims": [80, 74, 92, 76, 88, 62, 82, 80]},
    "apompliano": {"role": "Pomp Investments",
        "summary": "Making crypto mainstream — one podcast and newsletter at a time.",
        "dims": [80, 72, 96, 85, 86, 65, 78, 92]},
    "woonomic": {"role": "On-Chain Analyst",
        "summary": "The pioneer of on-chain Bitcoin analytics — data-driven conviction.",
        "dims": [82, 88, 88, 82, 84, 72, 90, 92]},
    "laurashin": {"role": "Crypto Journalist",
        "summary": "The most trusted voice in crypto journalism — decade of unbiased reporting.",
        "dims": [78, 80, 96, 72, 82, 65, 92, 94]},
    "adam3us": {"role": "Blockstream CEO",
        "summary": "Invented Hashcash, cited by Satoshi — one of Bitcoin's founding fathers.",
        "dims": [80, 95, 85, 90, 78, 72, 92, 85]},
    "nickszabo4": {"role": "Cryptographer",
        "summary": "Conceived smart contracts and Bit Gold — a true crypto OG.",
        "dims": [76, 96, 82, 88, 72, 70, 95, 88]},
    "erikvoorhees": {"role": "ShapeShift Founder",
        "summary": "DeFi pioneer championing financial sovereignty and decentralization.",
        "dims": [82, 80, 92, 90, 84, 68, 88, 86]},
    "cburniske": {"role": "Placeholder VC",
        "summary": "Wrote the book on crypto valuation — literally.",
        "dims": [80, 86, 90, 82, 84, 70, 90, 88]},
    "cathiedwood": {"role": "ARK Invest CEO",
        "summary": "Betting billions on the convergence of AI, crypto, and disruptive tech.",
        "dims": [80, 75, 92, 88, 86, 62, 82, 86]},
    "ilblackdragon": {"role": "NEAR Co-Founder",
        "summary": "Building NEAR — scalable blockchain with AI-native capabilities.",
        "dims": [88, 90, 86, 95, 88, 80, 82, 84]},

    # ════════════════════════════════════════
    #  AI Builders & Developers
    # ════════════════════════════════════════
    "swyx": {"role": "Latent Space Founder",
        "summary": "The voice of the AI engineering movement — bridging research and production.",
        "dims": [95, 88, 96, 90, 96, 92, 88, 97]},
    "levelsio": {"role": "Indie AI Builder",
        "summary": "Solo founder shipping viral AI products at impossible speed.",
        "dims": [96, 72, 92, 98, 96, 85, 70, 88]},
    "simonw": {"role": "AI Toolmaker",
        "summary": "Prolific builder and writer exploring every corner of practical AI.",
        "dims": [97, 88, 92, 96, 98, 90, 92, 96]},
    "realgeorgehotz": {"role": "Tiny Corp CEO",
        "summary": "Hacker-founder democratizing GPU computing with tinygrad.",
        "dims": [95, 94, 88, 97, 92, 86, 78, 82]},
    "mckaywrigley": {"role": "AI Developer",
        "summary": "Shipping AI-powered tools and teaching developers to build with LLMs.",
        "dims": [95, 85, 90, 94, 95, 92, 78, 93]},
    "emollick": {"role": "Wharton Professor",
        "summary": "The professor making AI practical for business — one experiment at a time.",
        "dims": [94, 85, 96, 78, 95, 90, 94, 98]},
    "bindureddy": {"role": "Abacus.AI CEO",
        "summary": "Building enterprise AI platforms that bring LLMs to production.",
        "dims": [92, 90, 88, 95, 90, 85, 82, 86]},
    "mattshumer_": {"role": "HyperWrite CEO",
        "summary": "Building AI writing tools and pushing agent capabilities forward.",
        "dims": [94, 86, 90, 95, 94, 92, 80, 88]},
    "scottswu": {"role": "Cognition Labs CEO",
        "summary": "Building the world's first AI software engineer — Devin.",
        "dims": [92, 92, 85, 98, 94, 90, 82, 80]},
    "clementdelangue": {"role": "Hugging Face CEO",
        "summary": "Democratizing AI with the world's largest open-source ML platform.",
        "dims": [93, 90, 96, 97, 94, 85, 88, 95]},
    "alexandr_wang": {"role": "Scale AI CEO",
        "summary": "Building the data infrastructure layer powering every major AI lab.",
        "dims": [88, 86, 90, 95, 90, 78, 85, 82]},
    "emostaque": {"role": "Stability AI Founder",
        "summary": "Championed open-source generative AI and brought Stable Diffusion to the world.",
        "dims": [90, 85, 92, 93, 92, 80, 82, 88]},
    "amasad": {"role": "Replit CEO",
        "summary": "Making coding accessible to everyone with AI-powered development.",
        "dims": [94, 86, 92, 97, 94, 90, 82, 92]},

    # ════════════════════════════════════════
    #  AI Content Creators & Educators
    # ════════════════════════════════════════
    "emaboringkass": {"role": "AI Content Creator",
        "summary": "Making AI accessible and fun for everyday audiences.",
        "dims": [85, 72, 90, 68, 82, 78, 88, 94]},
    "rohanpaul_ai": {"role": "AI Educator",
        "summary": "Breaking down complex AI papers into actionable insights.",
        "dims": [88, 90, 92, 75, 90, 85, 82, 96]},
    "chiefaioffice": {"role": "AI Newsletter",
        "summary": "Curating the most important AI developments for a massive audience.",
        "dims": [86, 78, 94, 72, 92, 80, 85, 95]},

    # ════════════════════════════════════════
    #  Crypto x AI Figures
    # ════════════════════════════════════════
    "shawmakesmagic": {"role": "ElizaOS Creator",
        "summary": "Pioneering the intersection of AI agents and crypto with ElizaOS.",
        "dims": [94, 85, 92, 96, 95, 88, 78, 90]},
    "dankvr": {"role": "AI Agent Builder",
        "summary": "Building at the frontier of AI agents and decentralized intelligence.",
        "dims": [90, 82, 88, 92, 90, 85, 78, 86]},
    "0xjeff": {"role": "AI x Crypto Leader",
        "summary": "Deep analysis at the convergence of AI agents and decentralized systems.",
        "dims": [88, 82, 92, 85, 90, 82, 80, 90]},
    "aixbt_agent": {"role": "AI Crypto Agent",
        "summary": "Autonomous AI agent analyzing crypto markets in real-time on X.",
        "dims": [92, 80, 90, 88, 94, 85, 75, 82]},

    # ════════════════════════════════════════
    #  Other Notable Tech Figures
    # ════════════════════════════════════════
    "jack": {"role": "Twitter Co-Founder",
        "summary": "Built Twitter and Square — now exploring Bitcoin and decentralized social.",
        "dims": [82, 72, 92, 95, 86, 65, 85, 78]},
    "billgates": {"role": "Microsoft Co-Founder",
        "summary": "From Microsoft to global health — now deeply engaged with AI's societal impact.",
        "dims": [82, 80, 90, 92, 82, 68, 92, 88]},
    "levie": {"role": "Box CEO",
        "summary": "Enterprise leader evangelizing AI adoption in the corporate world.",
        "dims": [90, 78, 94, 88, 92, 82, 84, 90]},
    "benedictevans": {"role": "Tech Analyst",
        "summary": "The sharpest pen in tech analysis — framing AI's impact with clarity.",
        "dims": [86, 82, 92, 72, 88, 75, 92, 94]},
    "noahpinion": {"role": "Economics Writer",
        "summary": "Bringing economic rigor to the AI debate — nuanced takes on tech and society.",
        "dims": [82, 80, 94, 68, 85, 72, 94, 96]},
    "stratechery": {"role": "Tech Strategist",
        "summary": "The most influential tech strategy newsletter — essential reading on AI business.",
        "dims": [88, 85, 90, 78, 90, 78, 94, 96]},
}

# Aliases — common alternate spellings or old handles
_ALIASES = {
    "samaltman": "sama", "andrejkarpathy": "karpathy",
    "darioamodei": "daboringkass", "danielaamodei": "daboringkassei",
    "ilyasutskever": "ilyasut", "changpengzhao": "cz_binance",
    "czpeng": "cz_binance", "cz": "cz_binance",
    "vitalik": "vitalikbuterin", "brianarmstrong": "brian_armstrong",
    "michaelsaylor": "saylor", "marcanborningkass": "pmarca",
    "marcandreessen": "pmarca", "elonmusk": "elonmusk",
    "timcook": "tim_cook", "reidhoffman": "reidhoffman",
    "georgehotz": "realgeorgehotz", "geohot": "realgeorgehotz",
    "drjimfan": "jimfan", "claboringkass": "clementdelangue",
    "pompliano": "apompliano", "pomp": "apompliano",
    "willywoo": "woonomic", "arthurhayes": "haaboringkass",
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


# ── Bio Fetching via fxtwitter (free, no auth) ──

def _fetch_bio(handle):
    """Fetch X profile data. Returns cached result or fetches from API.
    Result is saved to disk so the same handle always returns the same data."""
    h = handle.lower()
    cache_f = BIO_CACHE / f"{h}.json"
    if cache_f.exists():
        try:
            with open(cache_f) as f:
                return json.load(f)
        except Exception:
            pass

    try:
        req = urllib.request.Request(
            f"https://api.fxtwitter.com/{handle}",
            headers={"User-Agent": "HermesID/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                return None
            raw = json.loads(resp.read())
        u = raw.get("user", {})
        if not u:
            return None
        result = {
            "bio": u.get("description", ""),
            "name": u.get("name", ""),
            "followers": u.get("followers", 0),
            "following": u.get("following", 0),
            "tweets": u.get("tweets", 0),
        }
        with open(cache_f, "w") as f:
            json.dump(result, f)
        return result
    except Exception:
        return None


# ── Keyword-Based Dimension Scoring Engine ──
# Each dimension has keywords that boost the score for that dimension.
# High-signal keywords = +8, medium = +5, low = +3

_DIM_KEYWORDS = {
    "AI Usage": {
        "hi": ["chatgpt", "gpt-4", "claude", "gemini", "copilot", "midjourney",
               "stable diffusion", "dall-e", "llama", "grok", "perplexity",
               "cursor", "v0", "replit ai", "openai", "anthropic", "huggingface"],
        "md": ["ai tool", "ai-powered", "automation", "ai workflow", "generative ai",
               "ai agent", "llm", "model", "fine-tun"],
        "lo": ["tech", "digital", "software", "data", "cloud", "saas"],
    },
    "AI Understanding": {
        "hi": ["machine learning", "deep learning", "neural net", "transformer",
               "nlp", "computer vision", "reinforcement learning", "diffusion model",
               "attention mechanism", "embedding", "tokeniz", "inference",
               "phd", "researcher", "professor", "scientist", "arxiv", "paper"],
        "md": ["algorithm", "model", "benchmark", "dataset", "training",
               "fine-tun", "rag", "vector", "semantic", "latent", "foundation model"],
        "lo": ["ai", "ml", "data science", "analytics", "statistics"],
    },
    "Communication": {
        "hi": ["podcast", "newsletter", "keynote", "speaker", "author", "writer",
               "educator", "youtuber", "creator", "media", "journalist",
               "community", "evangelist", "advocate"],
        "md": ["blog", "content", "thread", "sharing", "teach", "mentor",
               "influencer", "host", "moderator", "contributor"],
        "lo": ["social", "twitter", "connect", "network", "engage"],
    },
    "Product Building": {
        "hi": ["founder", "co-founder", "ceo", "cto", "coo", "built", "building",
               "shipped", "launched", "startup", "company", "yc", "y combinator",
               "acquired", "raised", "series", "product", "app"],
        "md": ["developer", "engineer", "builder", "maker", "hacker",
               "open source", "contributor", "maintainer", "protocol"],
        "lo": ["project", "team", "lead", "head", "director", "manager",
               "vp", "partner", "advisor"],
    },
    "Adoption Speed": {
        "hi": ["early adopter", "day one", "beta tester", "bleeding edge",
               "frontier", "cutting edge", "first", "pioneer", "alpha"],
        "md": ["new", "latest", "emerging", "next", "future", "innovation",
               "disrupt", "experiment", "explore"],
        "lo": ["tech", "digital", "modern", "forward"],
    },
    "Prompt Engineering": {
        "hi": ["prompt engineer", "prompt", "chain of thought", "few-shot",
               "system prompt", "jailbreak", "instruction", "fine-tun"],
        "md": ["ai tool", "workflow", "automat", "template", "custom",
               "optimize", "pipeline", "agent"],
        "lo": ["power user", "expert", "advanced", "pro"],
    },
    "Critical Awareness": {
        "hi": ["ai safety", "alignment", "responsible ai", "ethics", "bias",
               "hallucination", "regulation", "governance", "risk", "trustworthy"],
        "md": ["privacy", "security", "fairness", "transparent", "accountab",
               "oversight", "policy", "compliance"],
        "lo": ["careful", "thoughtful", "critical", "aware", "consider"],
    },
    "Knowledge Sharing": {
        "hi": ["teacher", "professor", "educator", "course", "tutorial",
               "workshop", "bootcamp", "academy", "mentor", "open source"],
        "md": ["write", "blog", "share", "guide", "tips", "thread",
               "publish", "document", "contributor"],
        "lo": ["help", "community", "support", "learn", "resource"],
    },
}

def _score_bio_dims(bio, name, followers, following, tweets):
    """Score each AI dimension based on real profile data.
    Returns list of 8 scores and a detected role string.

    Scoring formula per dimension:
      score = base_from_followers + keyword_hits + activity_bonus
    Capped at 92 (only curated figures can reach 93+)."""
    text = f"{bio} {name}".lower()

    # Step 1: Follower-based base score (social proof = credibility)
    if followers >= 5000000:   f_base = 38
    elif followers >= 1000000: f_base = 33
    elif followers >= 500000:  f_base = 29
    elif followers >= 100000:  f_base = 25
    elif followers >= 50000:   f_base = 22
    elif followers >= 10000:   f_base = 18
    elif followers >= 5000:    f_base = 15
    elif followers >= 1000:    f_base = 12
    elif followers >= 100:     f_base = 8
    else:                      f_base = 5

    # Step 2: Keyword scoring per dimension
    kw_scores = []
    for dim_name in DIM_NAMES:
        kw = _DIM_KEYWORDS[dim_name]
        pts = 0
        for word in kw["hi"]:
            if word in text: pts += 10
        for word in kw["md"]:
            if word in text: pts += 6
        for word in kw["lo"]:
            if word in text: pts += 3
        kw_scores.append(min(pts, 50))

    total_kw = sum(kw_scores)
    # Global AI-relevance multiplier: more keywords = profile is more AI-native
    if total_kw >= 80:   kw_mult = 1.3
    elif total_kw >= 50: kw_mult = 1.15
    elif total_kw >= 25: kw_mult = 1.0
    elif total_kw >= 10: kw_mult = 0.85
    else:                kw_mult = 0.7

    # Step 3: Activity bonus from tweet volume
    if tweets >= 50000:   t_bonus = 8
    elif tweets >= 10000: t_bonus = 6
    elif tweets >= 5000:  t_bonus = 5
    elif tweets >= 1000:  t_bonus = 3
    elif tweets >= 100:   t_bonus = 2
    else:                 t_bonus = 0

    # Step 4: Assemble final dimension scores
    # idx: 0=Usage, 1=Understanding, 2=Communication, 3=ProductBuilding
    #      4=AdoptionSpeed, 5=PromptEng, 6=CriticalAwareness, 7=KnowledgeSharing
    dim_scores = []
    # Dimension-specific follower weight (some dims benefit more from reach)
    dim_follower_weight = [0.7, 0.5, 1.2, 0.8, 0.6, 0.4, 0.4, 1.0]
    for i, kw_s in enumerate(kw_scores):
        base = f_base * dim_follower_weight[i]
        adjusted_kw = kw_s * kw_mult
        raw = base + adjusted_kw + t_bonus
        final = max(12, min(92, round(raw + 15)))  # +15 floor offset
        dim_scores.append(final)

    # Detect role from bio keywords
    role = "AI Explorer"
    bio_l = bio.lower()
    role_checks = [
        ("founder", "Founder"), ("co-founder", "Co-Founder"),
        ("ceo", "CEO"), ("cto", "CTO"), ("coo", "COO"),
        ("professor", "Professor"), ("researcher", "Researcher"),
        ("engineer", "Engineer"), ("developer", "Developer"),
        ("designer", "Designer"), ("investor", "Investor"),
        ("partner", "VC Partner"), ("analyst", "Analyst"),
        ("journalist", "Journalist"), ("creator", "Creator"),
        ("builder", "Builder"), ("writer", "Writer"),
        ("trader", "Trader"), ("educator", "Educator"),
        ("advisor", "Advisor"), ("scientist", "Scientist"),
        ("director", "Director"), ("artist", "Artist"),
    ]
    for keyword, title in role_checks:
        if keyword in bio_l:
            role = title
            break

    return dim_scores, role


def _make_summary(bio, total, level, name):
    """Generate a contextual summary based on bio and score."""
    if not bio.strip():
        if total >= 80:
            return "A significant presence in the tech ecosystem."
        elif total >= 60:
            return "Actively engaging with technology and digital innovation."
        else:
            return "Exploring the digital landscape with growing potential."

    clean = bio.split("\n")[0].strip()
    if len(clean) > 80:
        clean = clean[:77] + "..."
    return clean


def gen_scores(handle):
    """Generate scores for a handle. Priority:
    1. Curated KNOWN_FIGURES database (84+ major figures)
    2. Real X bio analysis via fxtwitter API (cached for stability)
    3. Deterministic fallback for handles with no X data"""
    h = handle.lower()
    h = _ALIASES.get(h, h)

    # ── Tier 1: Known figure → curated data ──
    if h in KNOWN_FIGURES:
        fig = KNOWN_FIGURES[h]
        dims = [{"name": n, "score": s} for n, s in zip(DIM_NAMES, fig["dims"])]
        weights = [0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.10, 0.11]
        total = round(sum(s * w for s, w in zip(fig["dims"], weights)))
        return {
            "handle": h, "total_score": total,
            "level": score_to_level(total), "role": fig["role"],
            "summary": fig["summary"], "dimensions": dims,
        }

    # ── Tier 2: Fetch real X bio and score from it ──
    profile = _fetch_bio(h)
    if profile and profile.get("bio") is not None:
        raw_dims, role = _score_bio_dims(
            profile["bio"], profile.get("name", ""),
            profile.get("followers", 0),
            profile.get("following", 0),
            profile.get("tweets", 0))

        dims = [{"name": n, "score": s} for n, s in zip(DIM_NAMES, raw_dims)]
        weights = [0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.10, 0.11]
        total = round(sum(s * w for s, w in zip(raw_dims, weights)))
        level = score_to_level(total)
        summary = _make_summary(
            profile["bio"], total, level, profile.get("name", h))
        return {
            "handle": h, "total_score": total,
            "level": level, "role": role,
            "summary": summary, "dimensions": dims,
        }

    # ── Tier 3: No data available → deterministic fallback ──
    seed = _h(h)
    def rng():
        nonlocal seed
        seed = (seed * 16807) % 2147483647
        return (seed & 0x7FFFFFFF) / 2147483647

    base = 25 + int(rng() * 25)  # range 25-50
    dims = []
    for n in DIM_NAMES:
        variance = int(rng() * 20) - 10
        s = max(12, min(65, base + variance))
        dims.append({"name": n, "score": s})

    weights = [0.15, 0.15, 0.12, 0.15, 0.12, 0.10, 0.10, 0.11]
    total = round(sum(d["score"] * w for d, w in zip(dims, weights)))

    role_pool = [
        "AI Explorer", "AI Curious", "Digital Thinker",
        "Tech Enthusiast", "AI Observer",
    ]
    role = role_pool[seed % len(role_pool)]

    summary_pool = [
        "Exploring the AI landscape with growing curiosity.",
        "Beginning to navigate the possibilities of AI tools.",
        "Curious about AI's potential and open to learning more.",
    ]
    summary = summary_pool[seed % len(summary_pool)]

    return {
        "handle": h, "total_score": total,
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
    label_w = max(tw(d, lab, fb) for lab, _, _ in fields) + 12
    max_val_w = rx - RIGHT_X - label_w
    for label, val, vf in fields:
        d.text((RIGHT_X, ry), label, fill=BLACK, font=fb)
        if tw(d, val, vf) > max_val_w:
            for cut in range(1, len(val)):
                t = val[:len(val) - cut] + ".."
                if tw(d, t, vf) <= max_val_w:
                    val = t; break
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
