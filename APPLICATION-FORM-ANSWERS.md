# Swiggy Builders Club — Application Form Answers

> **Form URL**: https://forms.gle/4vkeKyqm15Qb6fnJA
> **Track**: Developer
> **Fill this in and submit. Takes ~5 minutes.**

---

## Form Fields (in order)

### 1. Full Name *
```
Himansh
```

### 2. Email *
```
[YOUR EMAIL ADDRESS]
```

### 3. Are you applying as… *
```
○ Individual Developer  ← Select this
○ Small Team (2–5)
○ Startup
```

### 4. Team / Project Name *
```
FoodDNA Agent
```

### 5. GitHub or Portfolio URL *
```
https://github.com/demo84431-ship-it/AI-video-editing
```

### 6. LinkedIn *
```
[YOUR LINKEDIN URL — or write "N/A" if you don't have one]
```

### 7. What are you building? (2–3 sentences) *
```
FoodDNA Agent is a psychology-first AI behavioral intelligence system that learns Indian users' food behavior patterns from Swiggy MCP signals and builds a comprehensive "Food DNA" — a multi-dimensional psychological profile capturing cultural identity, regional preferences, dietary patterns, temporal rhythms, emotional triggers, and social dynamics. It uses cross-server fusion (Food + Instamart + Dineout) to generate personalized recommendations grounded in 6 established behavioral frameworks. Built by a Psychology Master's graduate, it treats food as identity, not nutrition.
```

### 8. Which MCP servers do you need? *
```
☑ Swiggy Food
☑ Swiggy Instamart
☑ Swiggy Dineout
```

### 9. What type of integration is this? *
```
○ AI Agent / Copilot  ← Select this
○ Web App
○ Mobile App
○ Slack/Teams Bot
○ CLI Tool
○ Other
```

### 10. Tech stack & architecture overview *
```
Python 3.10+ with MCP Python SDK. OAuth 2.1 + PKCE for authentication. 
Architecture: 4-layer system — (1) MCP Signal Ingestion from all 3 Swiggy 
servers, (2) Behavioral Feature Extraction with per-tool extractors, 
(3) Food DNA Calculator using exponential moving average updates with 
per-dimension learning rates, (4) Psychology-Driven Recommendation Engine 
with 3 modes: proactive (time/pattern/festival), reactive (user-initiated), 
and cross-server (Food+Instamart+Dineout fusion). Includes Nudge Engine 
with psychological framing (Habit Loop, SDT, Nudge Theory, Stages of Change).
Voice (≤3 options) and chat (≤8 options) response shaping. Rate limited at 
100 req/min with exponential backoff retry.
```

### 11. Redirect URI(s) for auth flows *
```
http://localhost:3000/callback
```

### 12. Expected request volume *
```
○ < 1K/day  ← Select this (development phase)
○ 1K–10K/day
○ 10K–100K/day
○ Not sure yet
```

### 13. Demo link, GitHub repo, or anything else *
```
GitHub repo: https://github.com/demo84431-ship-it/AI-video-editing
(Full source code: 11 Python files, 3,500+ lines)

Demo video: [PASTE YOUR VIDEO LINK HERE — Loom/Google Drive/YouTube unlisted]

Key files:
- swiggy-builders/food-dna-agent/src/ — Full agent implementation
- swiggy-builders/food-dna-agent/design/01-food-dna-taxonomy.md — 10-dimension taxonomy
- swiggy-builders/food-dna-agent/technical/01-recommendation-engine.md — Algorithm design
- swiggy-builders/food-dna-agent/demo.py — Interactive demo script

What makes this different:
- Psychology-first: Built by a Psychology Master's graduate using 6 behavioral frameworks
- Cross-server fusion: Combines Food + Instamart + Dineout signals
- Indian-specific: 12 life-stage profiles, festival calendar, dietary identity as hard filter
- Ethical AI: Dietary identity never overridden, nudge suppression respects autonomy
```

### 14. I acknowledge Swiggy's MCP integration terms *
```
☑ Yes
```

---

## Before Submitting Checklist

- [ ] Fill in your email address
- [ ] Fill in your LinkedIn URL (or "N/A")
- [ ] Record and upload demo video (Loom/Google Drive/YouTube unlisted)
- [ ] Paste demo video link in field #13
- [ ] Review all answers
- [ ] Check "Yes" for terms acknowledgment
- [ ] Click Submit

## After Submitting

1. Wait for Swiggy to review (usually a few days)
2. You'll receive a staging `client_id` via email
3. Test against `mcp-staging.swiggy.com/{server}`
4. After 48h clean staging traffic → production `client_id`
5. Go live!

---

*Good luck! 🚀*
