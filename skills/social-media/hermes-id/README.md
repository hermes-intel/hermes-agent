# Hermes ID — AI Identification Card

**"Test your AI Native level."**

A Hermes Agent skill that scrapes any X/Twitter user's recent public tweets, analyzes their AI proficiency across 8 weighted dimensions using LLM reasoning, and generates a shareable card image.

Website: [hermesid.wtf](https://hermesid.wtf) · X: [@Hermes_ID](https://x.com/Hermes_ID)

## How It Works

1. **Input** — User provides an X handle (e.g. `@teknium`)
2. **Scrape** — Hermes Agent collects recent public tweets using browser tools
3. **Analyze** — LLM scores the user across 8 AI proficiency dimensions
4. **Generate** — Python script creates a shareable card image (PNG)
5. **Share** — User gets the card + a one-click share link for X

## 8 Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| AI Usage | 15% | Frequency and breadth of AI tool use |
| AI Understanding | 15% | Depth of technical AI knowledge |
| Communication | 12% | Quality of AI community engagement |
| Product Building | 15% | Actually building things with AI |
| Adoption Speed | 12% | How quickly they try new AI releases |
| Prompt Engineering | 10% | Sophistication of prompting techniques |
| Critical Awareness | 10% | Understanding of AI limitations and risks |
| Knowledge Sharing | 11% | Teaching others about AI |

## Level Thresholds

| Score | Level |
|-------|-------|
| 95–100 | Agent God |
| 88–94 | AI Native |
| 78–87 | AI Strategist |
| 65–77 | AI Explorer |
| 50–64 | AI Curious |
| 35–49 | AI Aware |
| 0–34 | AI Normie |

## Files

```
hermes-id/
├── SKILL.md                        # Hermes Skill definition (workflow + LLM prompt)
├── README.md                       # This file
├── requirements.txt                # Python dependencies (Pillow)
├── test_e2e.py                     # End-to-end pipeline test
└── references/
    ├── generate_card.py            # Card image generator (PIL/Pillow)
    └── scoring-rubric.md           # Detailed scoring criteria for each dimension
```

## Quick Start

### Card-Only Test (No API Key Needed)

Generate a sample card to verify the visual output:

```bash
cd skills/social-media/hermes-id

# Install dependency
pip install Pillow

# Generate a test card with sample scores
python3 test_e2e.py teknium --card-only

# Output: /tmp/hermes_id_teknium.png
```

### Full Pipeline (Requires LLM API Key)

Run the complete pipeline: scrape tweets → LLM analysis → card generation.

```bash
# Set one of these API keys:
export OPENAI_API_KEY="sk-..."
# or
export OPENROUTER_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-..."

# Run full pipeline
python3 test_e2e.py teknium

# Test with any handle
python3 test_e2e.py elonmusk
python3 test_e2e.py karpathy
```

### Scrape-Only Test

Test tweet scraping without LLM analysis:

```bash
python3 test_e2e.py teknium --scrape-only
```

> Note: Direct HTTP scraping of X often hits rate limits. In production, Hermes Agent uses its built-in `browser_navigate` + `browser_snapshot` tools for reliable scraping.

### Use the Card Generator Directly

If you have your own score data:

```bash
# Create a score JSON file
cat > /tmp/score.json << 'EOF'
{
  "handle": "yourhandle",
  "total_score": 85,
  "level": "AI Strategist",
  "role": "AI Architect",
  "summary": "A hands-on builder shipping AI tools at the frontier.",
  "dimensions": [
    {"name": "AI Usage", "score": 90, "justification": "..."},
    {"name": "AI Understanding", "score": 88, "justification": "..."},
    {"name": "Communication", "score": 75, "justification": "..."},
    {"name": "Product Building", "score": 92, "justification": "..."},
    {"name": "Adoption Speed", "score": 85, "justification": "..."},
    {"name": "Prompt Engineering", "score": 78, "justification": "..."},
    {"name": "Critical Awareness", "score": 70, "justification": "..."},
    {"name": "Knowledge Sharing", "score": 82, "justification": "..."}
  ]
}
EOF

# Generate the card
python3 references/generate_card.py /tmp/score.json /tmp/my_card.png

# Output: /tmp/my_card.png + /tmp/my_card.html (share page)
```

## Using with Hermes Agent

Install the skill in Hermes Agent, then simply provide a handle in chat:

```
> @teknium
```

Or be explicit:

```
> Score @elonmusk's AI level
> Generate an AI ID card for @karpathy
> Test my AI native level: @myhandle
```

Hermes Agent will automatically activate this skill, scrape tweets, run LLM analysis, generate the card, and present results with a share link.

## Card Features

- **Real X avatar** — Fetched via [unavatar.io](https://unavatar.io) (free, no API key needed)
- **Halftone manga filter** — Applied to the avatar for a distinctive visual style
- **8-axis radar chart** — Visual overview of all dimensions
- **Progress bars** — Detailed breakdown of each score
- **Personalized summary** — One-line shareable insight
- **Unique barcode** — Deterministic per handle
- **Share CTA** — Encourages viral sharing on X
- **One-click share** — Pre-filled tweet with @Hermes_ID tag

## Website

The companion website at [hermesid.wtf](https://hermesid.wtf) provides:

- Interactive card gallery with example AI leaders
- "Get Your Card" — enter any handle to generate a card instantly
- Share on X with Twitter Card previews
- Download card as PNG

See [`site/`](../../../site/) for website deployment instructions.
