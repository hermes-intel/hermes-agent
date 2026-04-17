---
name: hermes-id
description: "AI Identification Card — scrape any X/Twitter handle's recent tweets, score their AI proficiency across 8 dimensions with LLM analysis, and generate a shareable card image."
version: 1.0.0
author: Hermes ID
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
metadata:
  hermes:
    tags: [ai-score, x, twitter, social-media, identification, card, analysis, viral]
    homepage: https://hermesid.wtf
    related_skills: [xitter]
---

# Hermes ID — AI Identification Card

**"Test your AI Native level."**

Scrape any X/Twitter user's recent public tweets, analyze their AI proficiency across 8 weighted dimensions using LLM reasoning, and generate a shareable card image — all in one step.

## When to Activate

Activate when the user:

- Provides an X/Twitter handle (`@teknium`, `teknium`, etc.)
- Asks to "test", "score", "evaluate", or "rate" someone's AI level
- Asks for an "AI score", "AI card", "AI ID", or "Hermes ID"
- Says something like "测测 AI 水平", "AI Native level", or "generate an AI card for @xxx"

## Complete Workflow

### Step 1 — Parse Handle

Extract the X handle from the user's message. Strip the leading `@` if present. Normalize to lowercase. Tell the user you're starting the analysis.

### Step 2 — Scrape Recent Tweets

Collect the user's **recent public tweets** — aim for the last 30–90 days, minimum 20 tweets. Try these methods in order:

**Method A — `web_extract` (fastest)**

```
web_extract(urls=["https://x.com/{handle}"])
```

If this returns substantive tweet text (not just UI chrome), proceed.

**Method B — Browser tools (most reliable for X)**

If `web_extract` returns little useful content:

1. `browser_navigate("https://x.com/{handle}")`
2. Wait for load, then `browser_snapshot()` — captures visible tweets as text
3. `browser_scroll("down")` then `browser_snapshot()` — repeat 3–4 times to load more tweets
4. Concatenate all snapshot text

**Method C — Nitter fallback**

If X rate-limits or blocks:

```
web_extract(urls=["https://nitter.privacydev.net/{handle}"])
```

From the raw content, **extract only tweet text**. Strip navigation elements, ads, promoted content, and UI boilerplate. Keep: tweet body text, dates, and any visible engagement metrics (likes, retweets, reply counts).

If fewer than 10 tweets are found, warn the user that the analysis may be less accurate.

### Step 3 — LLM Scoring

Feed the collected tweets to the scoring prompt below. This is the core analysis — read every tweet carefully and reason about each dimension before assigning scores.

**Consult the detailed rubric** in `references/scoring-rubric.md` (use `skill_view(name="hermes-id", file_path="references/scoring-rubric.md")`) for precise definitions and examples.

Use this prompt structure (replace `{TWEETS}` with the collected content):

---

You are an expert AI analyst performing a deep evaluation of a Twitter/X user's AI proficiency. Below are their recent public tweets.

**TWEETS:**
```
{TWEETS}
```

**TASK:** Analyze these tweets and score the user across 8 dimensions. For each dimension, read through ALL tweets and identify specific evidence. Quote relevant tweets when possible. Then assign a score from 0 to 100.

**DIMENSIONS AND WEIGHTS:**

1. **AI Usage** (weight: 15%) — Frequency and breadth of actual AI tool use. Evidence: mentions of ChatGPT, Claude, Gemini, Midjourney, Cursor, Copilot, Stable Diffusion, Whisper, specific model names (GPT-4, Opus, Sonnet, Llama, Mistral, etc.), API usage, workflow automation.

2. **AI Understanding** (weight: 15%) — Depth of technical AI knowledge. Evidence: discussion of architectures (transformers, diffusion, MoE), training methods (RLHF, DPO, GRPO), benchmarks (MMLU, HumanEval), papers, model internals, tokenization, inference optimization, fine-tuning.

3. **Communication** (weight: 12%) — Quality of AI community engagement. Evidence: thoughtful replies to AI researchers/builders, being quoted/retweeted on AI topics, quality discussions, engaging with other AI practitioners, constructive debates.

4. **Product Building** (weight: 15%) — Actually building with AI. Evidence: shipping products/tools/agents, open-source contributions, project demos, GitHub links, "I built X with Y", integration of AI into real workflows, plugin/extension development.

5. **Adoption Speed** (weight: 12%) — How quickly they try new AI releases. Evidence: early mentions of newly released models/tools, day-one reactions, beta access usage, trying experimental features, being among the first to comment on new releases.

6. **Prompt Engineering** (weight: 10%) — Sophistication of prompting. Evidence: sharing advanced prompts, system prompt design, chain-of-thought usage, few-shot examples, structured output formatting, prompt optimization tips, meta-prompting.

7. **Critical Awareness** (weight: 10%) — Understanding of AI limitations. Evidence: discussing hallucinations, bias, safety concerns, alignment, responsible AI, failure modes, when NOT to use AI, nuanced takes on AI hype vs reality.

8. **Knowledge Sharing** (weight: 11%) — Teaching others about AI. Evidence: tutorials, tips threads, educational content, step-by-step guides, explaining concepts, mentoring, creating learning resources, "How to use X" posts.

**SCORING GUIDE:**
- 90–100: World-class, among the best on the platform in this dimension
- 75–89: Very strong, clearly above average
- 60–74: Solid, regularly demonstrates this
- 40–59: Moderate, occasional evidence
- 20–39: Minimal evidence
- 0–19: No evidence found

**LEVEL THRESHOLDS** (based on weighted total):
- 95–100: Agent God
- 88–94: AI Native
- 78–87: AI Strategist
- 65–77: AI Explorer
- 50–64: AI Curious
- 35–49: AI Aware
- 0–34: AI Normie

**ROLE:** Assign ONE creative title that best fits their profile. Choose from or create similar to: "Hermes Creator", "Prompt Whisperer", "Agent Architect", "Neural Navigator", "AI Evangelist", "Tool Curator", "Data Alchemist", "Tech Pioneer", "Code Alchemist", "Model Explorer", "AI Strategist", "Digital Craftsman", "Pattern Seeker", "Open-Source Champion", "AI Educator", "Frontier Scout".

**SUMMARY:** Write ONE punchy, shareable sentence (max 120 chars) about this user's AI profile. Make it specific and memorable — something they'd want to post.

**RESPOND IN THIS EXACT JSON FORMAT:**

```json
{
  "handle": "the_handle",
  "dimensions": [
    {"name": "AI Usage", "score": 85, "justification": "Frequently mentions Claude, Cursor, and Midjourney in daily workflow tweets. Shared 12+ posts about specific tool comparisons."},
    {"name": "AI Understanding", "score": 90, "justification": "Deep discussion of transformer architectures, referenced 3 papers, explained MoE routing in detail."},
    {"name": "Communication", "score": 75, "justification": "Active in AI Twitter conversations, quality replies to researchers, but limited original discussion threads."},
    {"name": "Product Building", "score": 88, "justification": "Shipped 2 AI-powered tools, shared GitHub repos, demo videos of agent workflows."},
    {"name": "Adoption Speed", "score": 82, "justification": "Tweeted about GPT-4o within hours of release, tried Gemini 2.0 on day one."},
    {"name": "Prompt Engineering", "score": 70, "justification": "Shared a few system prompts, but no advanced techniques like meta-prompting."},
    {"name": "Critical Awareness", "score": 65, "justification": "Occasionally mentions hallucination risks, but rarely dives deep into safety/alignment."},
    {"name": "Knowledge Sharing", "score": 78, "justification": "Published 3 tutorial threads, regularly explains concepts to followers."}
  ],
  "total_score": 80,
  "level": "AI Expert",
  "role": "Tool Curator",
  "summary": "A hands-on builder who ships AI tools fast and isn't afraid to go deep on the tech."
}
```

Calculate `total_score` as the weighted average: `sum(score * weight) / sum(weights)`. Round to the nearest integer.

---

Parse the JSON response. If the response isn't valid JSON, ask the model to fix it.

### Step 4 — Generate Card Image

Generate the shareable card PNG using the bundled Python script.

1. **Ensure Pillow is installed:**
   ```bash
   python3 -m pip install Pillow -q 2>/dev/null || true
   ```

2. **Write the score JSON to a temp file:**
   ```bash
   cat > /tmp/hermes_id_score.json << 'SCORE_EOF'
   {paste the JSON from Step 3}
   SCORE_EOF
   ```

3. **Locate and run the card generator:**

   The script is bundled with this skill. Find it at one of these paths:
   ```bash
   # If installed via Hermes
   python3 ~/.hermes/skills/social-media/hermes-id/references/generate_card.py /tmp/hermes_id_score.json /tmp/hermes_id_card.png

   # If running from repo checkout
   python3 skills/social-media/hermes-id/references/generate_card.py /tmp/hermes_id_score.json /tmp/hermes_id_card.png
   ```

   If neither path works, read the script with `skill_view(name="hermes-id", file_path="references/generate_card.py")`, write it to `/tmp/generate_card.py`, and run from there.

4. The card image will be saved at `/tmp/hermes_id_card.png`.

### Step 5 — Present Results

Return to the user:

1. **Attach the card image** (`/tmp/hermes_id_card.png`)

2. **Text summary:**
   ```
   AI Identification Card — @{handle}
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   AI Score: {total_score}/100 — {level}
   Role: {role}

   {summary}

   ┌─────────────────────────────┐
   │ AI Usage            {score} │
   │ AI Understanding    {score} │
   │ Communication       {score} │
   │ Product Building    {score} │
   │ Adoption Speed      {score} │
   │ Prompt Engineering  {score} │
   │ Critical Awareness  {score} │
   │ Knowledge Sharing   {score} │
   └─────────────────────────────┘

   Powered by Hermes Agent · hermesid.wtf
   ```

3. **One-click share link** — provide a ready-to-tweet URL:
   ```
   https://twitter.com/intent/tweet?text=My%20AI%20Score%3A%20{score}%2F100%20%E2%80%94%20{level}%20%F0%9F%A7%A0%0A%0AJust%20got%20my%20AI%20Identification%20Card%20from%20%40Hermes_ID%20%F0%9F%92%A1%0A%0AThink%20you%20can%20beat%20me%3F%20Test%20yours%20%E2%AC%87%EF%B8%8F%0Ahermesid.wtf
   ```
   Tell the user: **"Click this link to share on X — just attach your card image and post!"**

4. **Call to action:**
   > Share your card on X! Tag @Hermes_ID and challenge your friends — just send me any @handle to test theirs.

## Important Notes

- **Public data only.** Never attempt to access private/protected accounts.
- **Honest scoring.** Do not inflate scores. A user with no AI-related tweets should score low. The value of the tool depends on accurate, credible scores.
- **Quote evidence.** When presenting the text summary, cite 1-2 specific tweets as evidence for the strongest and weakest dimensions.
- **Low tweet count.** If fewer than 10 tweets are scraped, note this clearly: "Based on limited data — score may not reflect full AI proficiency."
- **Caching.** If analyzing the same handle again within 24 hours, mention the previous score and note any changes.
