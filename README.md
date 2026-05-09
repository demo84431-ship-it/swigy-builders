# Food DNA Agent — Project Overview

> **Builder**: Psychology Master's graduate
> **Platform**: Swiggy Builders Club (MCP)
> **Track**: Developer (with potential Enterprise evolution)
> **Status**: Phase 0-5 ✅ ALL COMPLETE — Ready for application submission
> **Deployed**: https://fooddna-agent-01.up.railway.app/

---

## What Is Food DNA Agent?

An AI agent that learns Indian users' food behavior patterns from Swiggy MCP signals and builds a comprehensive "Food DNA" — a behavioral profile that captures cultural identity, regional preferences, dietary patterns, temporal rhythms, emotional triggers, and social dynamics.

**Not just "what you like to eat" — but "why you eat what you eat, when you eat it, and how it connects to who you are."**

---

## Why This Project?

### Technical Differentiation
- Uses ALL behavioral signals across 3 MCP servers (`your_go_to_items`, `get_food_orders`, `get_booking_status`, `get_addresses`)
- Cross-server behavioral fusion — no one else combines grocery + food + dining patterns
- Gets smarter over time — learning agent, not static recommendation
- Voice-first design with behavioral intelligence

### Psychology Differentiation
- Built by someone who understands behavioral science, cognitive biases, and decision-making
- Applies established psychological frameworks (Habit Loop, Self-Determination Theory, Stages of Change)
- Models food as identity, not just nutrition
- Indian-specific behavioral model (regional, religious, familial, cultural)

### Strategic Differentiation
- Directly advances Swiggy's priorities: Instamart growth, Swiggy One retention, AI-first strategy
- Creates intelligence from data that competitors CAN'T access (no API = no behavioral signals)
- Demonstrates MCP mastery — cross-server composition, voice patterns, error handling

---

## Project Structure

```
food-dna-agent/
├── README.md                      ← You are here
├── app.py                         ← FastAPI web server (Railway deployment)
├── demo.py                        ← Interactive terminal demo (5 scenarios)
├── generate_video.py              ← PIL-based demo video generator
├── Procfile / railway.toml        ← Railway deployment config
├── APPLICATION-FORM-ANSWERS.md    ← Pre-filled Swiggy application
├── IMPLEMENTATION-PLAN.md         ← 5-phase build plan
├── profiles/                      ← 5 diverse user profiles
│   ├── arjun.json                 ← South Indian IT Professional
│   ├── priya.json                 ← North Indian Joint Family
│   ├── riya.json                  ← Bengali College Student
│   ├── shah.json                  ← Gujarati Senior Citizen (Jain)
│   └── karthik.json               ← NRI Remote Ordering
├── src/                           ← Agent implementation
│   ├── agent.py                   ← Main orchestrator
│   ├── food_dna.py                ← 10-dimension data model
│   ├── food_dna_calculator.py     ← EMA-based profile builder
│   ├── recommender.py             ← 10-factor scoring engine
│   ├── feature_extractor.py       ← MCP signal → behavioral features
│   ├── nudge_engine.py            ← Ethical nudge framework
│   ├── mcp_client.py              ← OAuth 2.1 + MCP client
│   └── config.py                  ← Configuration
├── static/
│   └── index.html                 ← Chat UI with profile selector, rich cards, voice
├── design/
│   ├── 01-food-dna-taxonomy.md    ← 10 dimensions, scoring, profiles
│   ├── 02-demo-and-application.md ← Demo scenarios, video script
│   └── 03-phase5-plan.md          ← Multi-profile, voice, chat enhancement
├── research/
│   ├── 01-indian-food-psychology.md
│   └── 06-life-stage-profiles.md
└── technical/
    ├── 01-recommendation-engine.md
    └── 02-agent-implementation.md
```

---

## Research Summary

### Indian Food Psychology (01)
- Food as identity (not nutrition) — cultural, regional, religious, familial dimensions
- 5-layer dietary framework: Religious → Regional → Family → Temporal → Emotional
- Habit loops in Indian context (Friday biryani, rain pakora, festival sweets)
- Behavioral biases: Status quo bias (strong), social proof (very strong), loss aversion
- Regional ordering patterns (South vs North vs West vs East India)
- Maslow's hierarchy, Self-Determination Theory, and Stages of Change applied to food

### Technical Foundation (02)
- IFCT 2017: 542 Indian foods, 38+ nutrients, 6 regions, multilingual names
- INDB: 1,016 Indian recipes with nutrition data
- Kaggle: 50K Indian food orders with behavior data
- Hybrid recommendation system architecture (collaborative + content-based)
- Time series forecasting for order prediction
- MCP Python SDK for Swiggy integration

---

## The Food DNA Model

### What Makes Up Someone's "Food DNA"?

| Dimension | Signals from MCP | Psychological Framework |
|-----------|-----------------|----------------------|
| **Cultural Identity** | Vegetarian/non-veg, cuisine preferences | Identity theory |
| **Regional Identity** | Food choices, spice levels, rice vs wheat | Cultural psychology |
| **Dietary Patterns** | Go-to items, order frequency | Habit loop theory |
| **Temporal Rhythm** | Order times, day-of-week patterns | Chronobiology |
| **Price Psychology** | Coupon usage, AOV patterns | Behavioral economics |
| **Health Orientation** | Food categories, calorie patterns | Health belief model |
| **Social Dynamics** | Solo vs family orders, group patterns | Social psychology |
| **Emotional Triggers** | Comfort food patterns, celebration food | Emotional regulation |
| **Life Stage** | Food choices reflect life stage | Developmental psychology |

### How Food DNA Gets Built

```
MCP Signals → Feature Extraction → Behavioral Profiling → Food DNA → Intelligent Agent

your_go_to_items     → Grocery patterns, brand preferences, dietary identity
get_food_orders      → Cuisine preferences, restaurant loyalty, ordering rhythm
get_booking_status   → Dining frequency, occasion types, social patterns
get_addresses        → Location context (home, work, travel, visiting)
```

---

## What's Built

### Phase 0-4: Core Agent ✅
- 10-dimension Food DNA model with psychological grounding
- MCP client with OAuth 2.1 + PKCE for all 3 Swiggy servers
- Feature extraction from behavioral signals
- EMA-based profile calculator with per-dimension learning rates
- 10-factor recommendation engine with dietary hard filters
- Ethical nudge engine with suppression rules
- Interactive terminal demo with 5 scenarios
- Railway deployment with demo mode

### Phase 5: Multi-Profile, Chat Enhancement, Voice ✅
- **5 diverse profiles**: Arjun, Priya, Riya, Mr. Shah, Karthik — each with full 10-dimension DNA
- **Profile selector UI**: Landing page with cards, profile switching
- **Rich cards**: Structured recommendations with images, ratings, prices, action buttons
- **Context-aware suggestions**: 6 suggestion sets that update based on conversation
- **Voice agent**: TTS (Listen button) + STT (mic input) — browser-native, zero server cost
- **Dark/light mode**: Toggle with localStorage persistence

## Next Steps

1. **Record demo video** — Show profile switching, rich cards, voice interaction
2. **Submit application** — Apply at https://mcp.swiggy.com/builders/access/
3. **Get Swiggy client_id** — Switch from demo mode to real MCP data
4. **Test with real users** — Validate Food DNA model against actual ordering behavior

---

## Key Contacts

- **Swiggy Builders**: builders@swiggy.in
- **Apply**: https://mcp.swiggy.com/builders/access/
- **Docs**: https://mcp.swiggy.com/builders/docs/
