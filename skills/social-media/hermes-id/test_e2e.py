#!/usr/bin/env python3
"""
Hermes ID — End-to-End Pipeline Test

Demonstrates the full pipeline: tweets → LLM analysis → card generation.

Usage:
    # Full pipeline with real LLM analysis (requires API key):
    OPENROUTER_API_KEY=sk-... python3 test_e2e.py teknium

    # Card-only test (skip LLM, use sample scores):
    python3 test_e2e.py teknium --card-only

    # Scrape tweets only (test scraping without LLM):
    python3 test_e2e.py teknium --scrape-only
"""

from __future__ import annotations

import json
import os
import sys
import re
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CARD_SCRIPT = SCRIPT_DIR / "references" / "generate_card.py"
SCORING_PROMPT_PATH = SCRIPT_DIR / "SKILL.md"


# ── Tweet Scraping ──────────────────────────────────────────────────

NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.cz",
    "https://xcancel.com",
]


def scrape_nitter(handle: str) -> list[str]:
    """Try scraping tweets from Nitter instances."""
    for base in NITTER_INSTANCES:
        url = f"{base}/{handle}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        try:
            resp = urllib.request.urlopen(req, timeout=12)
            html = resp.read().decode("utf-8", errors="ignore")
            tweets = re.findall(
                r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>',
                html, re.DOTALL,
            )
            if tweets:
                cleaned = [re.sub(r"<[^>]+>", "", t).strip() for t in tweets]
                cleaned = [t for t in cleaned if len(t) > 10]
                if cleaned:
                    print(f"  [nitter] {base} → {len(cleaned)} tweets")
                    return cleaned
        except Exception as e:
            print(f"  [nitter] {base} → {e}")
    return []


def scrape_syndication(handle: str) -> list[str]:
    """Try the X syndication timeline endpoint."""
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=12)
        html = resp.read().decode("utf-8", errors="ignore")
        texts = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        cleaned = [re.sub(r"<[^>]+>", "", t).strip() for t in texts]
        cleaned = [t for t in cleaned if len(t) > 20]
        if cleaned:
            print(f"  [syndication] → {len(cleaned)} tweets")
            return cleaned
    except Exception as e:
        print(f"  [syndication] → {e}")
    return []


def scrape_tweets(handle: str) -> list[str]:
    """Try all scraping methods; return list of tweet texts."""
    print(f"\n[Step 2] Scraping tweets for @{handle}...")

    tweets = scrape_nitter(handle)
    if tweets:
        return tweets

    tweets = scrape_syndication(handle)
    if tweets:
        return tweets

    print("  All live scraping methods failed (X rate limits).")
    print("  In production, Hermes Agent uses browser_navigate + browser_snapshot.")
    return []


# ── LLM Analysis ────────────────────────────────────────────────────

SCORING_PROMPT = """You are an expert AI analyst performing a deep evaluation of a Twitter/X user's AI proficiency. Below are their recent public tweets.

**TWEETS:**
```
{tweets}
```

**TASK:** Analyze these tweets and score the user across 8 dimensions. For each dimension, identify specific evidence from the tweets. Then assign a score from 0 to 100.

**DIMENSIONS AND WEIGHTS:**
1. **AI Usage** (15%) — Frequency and breadth of AI tool use
2. **AI Understanding** (15%) — Depth of technical AI knowledge
3. **Communication** (12%) — Quality of AI community engagement
4. **Product Building** (15%) — Actually building with AI
5. **Adoption Speed** (12%) — How quickly they try new AI releases
6. **Prompt Engineering** (10%) — Sophistication of prompting
7. **Critical Awareness** (10%) — Understanding of AI limitations
8. **Knowledge Sharing** (11%) — Teaching others about AI

**SCORING GUIDE:**
- 90-100: World-class  - 75-89: Very strong  - 60-74: Solid
- 40-59: Moderate  - 20-39: Minimal  - 0-19: No evidence

**LEVELS:** 95-100: Agent God, 88-94: AI Native, 78-87: AI Strategist, 65-77: AI Explorer, 50-64: AI Curious, 35-49: AI Aware, 0-34: AI Normie

Calculate total_score as weighted average. Assign a creative role title and a one-sentence shareable summary.

**RESPOND IN THIS EXACT JSON FORMAT (no other text):**
```json
{{
  "handle": "{handle}",
  "dimensions": [
    {{"name": "AI Usage", "score": 85, "justification": "..."}},
    {{"name": "AI Understanding", "score": 90, "justification": "..."}},
    {{"name": "Communication", "score": 75, "justification": "..."}},
    {{"name": "Product Building", "score": 88, "justification": "..."}},
    {{"name": "Adoption Speed", "score": 82, "justification": "..."}},
    {{"name": "Prompt Engineering", "score": 70, "justification": "..."}},
    {{"name": "Critical Awareness", "score": 65, "justification": "..."}},
    {{"name": "Knowledge Sharing", "score": 78, "justification": "..."}}
  ],
  "total_score": 80,
  "level": "AI Expert",
  "role": "Tool Curator",
  "summary": "One punchy sentence about this user's AI profile."
}}
```"""


def analyze_with_llm(handle: str, tweets: list[str]) -> dict | None:
    """Send tweets to an LLM for scoring. Tries OpenRouter, then OpenAI."""
    tweet_text = "\n---\n".join(tweets[:40])
    prompt = SCORING_PROMPT.format(tweets=tweet_text, handle=handle)

    # Try OpenRouter first, then OpenAI
    configs = []
    if os.environ.get("OPENROUTER_API_KEY"):
        configs.append({
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key": os.environ["OPENROUTER_API_KEY"],
            "model": "anthropic/claude-sonnet-4",
            "name": "OpenRouter",
        })
    if os.environ.get("OPENAI_API_KEY"):
        configs.append({
            "url": "https://api.openai.com/v1/chat/completions",
            "key": os.environ["OPENAI_API_KEY"],
            "model": "gpt-4o",
            "name": "OpenAI",
        })
    if os.environ.get("ANTHROPIC_API_KEY"):
        configs.append({
            "url": "https://api.anthropic.com/v1/messages",
            "key": os.environ["ANTHROPIC_API_KEY"],
            "model": "claude-sonnet-4-20250514",
            "name": "Anthropic",
        })

    if not configs:
        print("  No API key found. Set OPENROUTER_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY.")
        return None

    for cfg in configs:
        print(f"  Calling {cfg['name']} ({cfg['model']})...")
        try:
            if cfg["name"] == "Anthropic":
                body = json.dumps({
                    "model": cfg["model"],
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                }).encode()
                req = urllib.request.Request(cfg["url"], data=body, headers={
                    "Content-Type": "application/json",
                    "x-api-key": cfg["key"],
                    "anthropic-version": "2023-06-01",
                })
            else:
                body = json.dumps({
                    "model": cfg["model"],
                    "messages": [
                        {"role": "system", "content": "You are an AI proficiency analyst. Respond only with valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                }).encode()
                req = urllib.request.Request(cfg["url"], data=body, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {cfg['key']}",
                })

            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read())

            if cfg["name"] == "Anthropic":
                text = result["content"][0]["text"]
            else:
                text = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                score_data = json.loads(json_match.group())
                print(f"  Success! Score: {score_data.get('total_score')}/100")
                return score_data

        except Exception as e:
            print(f"  {cfg['name']} failed: {e}")

    return None


# ── Card Generation ─────────────────────────────────────────────────

def generate_card(score_data: dict, handle: str) -> str:
    """Run the card generator script."""
    json_path = f"/tmp/hermes_id_score_{handle}.json"
    png_path = f"/tmp/hermes_id_{handle}.png"

    with open(json_path, "w") as f:
        json.dump(score_data, f, indent=2)

    # Import and run directly
    sys.path.insert(0, str(SCRIPT_DIR / "references"))
    from generate_card import generate
    generate(score_data, png_path)

    return png_path


# ── Main ────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_e2e.py <handle> [--card-only] [--scrape-only]")
        print("\nEnvironment variables:")
        print("  OPENROUTER_API_KEY  — for LLM analysis via OpenRouter")
        print("  OPENAI_API_KEY      — for LLM analysis via OpenAI")
        print("  ANTHROPIC_API_KEY   — for LLM analysis via Anthropic")
        sys.exit(1)

    handle = sys.argv[1].lstrip("@").lower()
    card_only = "--card-only" in sys.argv
    scrape_only = "--scrape-only" in sys.argv

    print(f"{'='*50}")
    print(f"  Hermes ID — E2E Pipeline Test")
    print(f"  Handle: @{handle}")
    print(f"{'='*50}")

    # ── Step 1: Parse handle ──
    print(f"\n[Step 1] Handle: @{handle}")

    if card_only:
        # Use sample scores for card-only test
        print("\n[Step 2-3] Skipped (--card-only mode)")
        score_data = {
            "handle": handle,
            "total_score": 92,
            "level": "Agent God",
            "role": "Hermes Creator",
            "dimensions": [
                {"name": "AI Usage", "score": 95, "justification": "Sample data"},
                {"name": "AI Understanding", "score": 93, "justification": "Sample data"},
                {"name": "Communication", "score": 88, "justification": "Sample data"},
                {"name": "Product Building", "score": 96, "justification": "Sample data"},
                {"name": "Adoption Speed", "score": 90, "justification": "Sample data"},
                {"name": "Prompt Engineering", "score": 85, "justification": "Sample data"},
                {"name": "Critical Awareness", "score": 82, "justification": "Sample data"},
                {"name": "Knowledge Sharing", "score": 94, "justification": "Sample data"},
            ],
            "summary": f"@{handle} — sample card for layout testing.",
        }
    else:
        # ── Step 2: Scrape ──
        tweets = scrape_tweets(handle)

        if scrape_only:
            if tweets:
                print(f"\n--- Scraped {len(tweets)} tweets ---")
                for i, t in enumerate(tweets[:10]):
                    print(f"  {i+1}. {t[:120]}...")
            else:
                print("\n  No tweets scraped. X may be rate-limiting.")
            return

        if not tweets:
            print("\n  No tweets scraped. Using fallback: provide tweets manually.")
            print("  Paste tweets below (one per line, blank line to finish):")
            tweets = []
            while True:
                line = input().strip()
                if not line:
                    break
                tweets.append(line)
            if not tweets:
                print("  No tweets provided. Exiting.")
                return

        print(f"  Collected {len(tweets)} tweets.")

        # ── Step 3: LLM Analysis ──
        print(f"\n[Step 3] Running LLM analysis...")
        score_data = analyze_with_llm(handle, tweets)
        if not score_data:
            print("  LLM analysis failed. Run with --card-only for a test card.")
            return

    # ── Step 4: Generate card ──
    print(f"\n[Step 4] Generating card image...")
    png_path = generate_card(score_data, handle)

    # ── Step 5: Results ──
    print(f"\n[Step 5] Results")
    print(f"{'='*50}")
    print(f"  AI Identification Card — @{handle}")
    print(f"  AI Score: {score_data['total_score']}/100 — {score_data['level']}")
    print(f"  Role: {score_data['role']}")
    print(f"  {score_data.get('summary', '')}")
    print()
    for dim in score_data["dimensions"]:
        j = dim.get("justification", "")
        suffix = f" — {j[:80]}" if j and j != "Sample data" else ""
        print(f"  {dim['name']:.<25} {dim['score']}{suffix}")
    print()
    print(f"  Card saved: {png_path}")
    print(f"{'='*50}")
    print(f"  Powered by Hermes Agent · hermesid.wtf")


if __name__ == "__main__":
    main()
