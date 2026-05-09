# Food DNA Agent — Phased Implementation Plan

> **Date**: 2026-05-09
> **Builder**: Psychology Master's graduate
> **Platform**: Swiggy Builders Club (MCP)
> **Status**: Phase 0 — ✅ | Phase 1 — ✅ | Phase 2 — ✅ | Phase 3 — ✅ | Phase 4 — ✅ | Phase 5 — ✅ ALL COMPLETE

---

## Overview

The Food DNA Agent is built in 5 phases. Each phase is completed fully before moving to the next. Each phase ends with a GitHub push.

```
Phase 0: Research Gap Fill          ← ✅ Complete
Phase 1: Food DNA Taxonomy Design   ← ✅ Complete
Phase 2: Recommendation Engine      ← ✅ Complete
Phase 3: MCP Integration & Agent    ← ✅ Complete
Phase 4: Demo & Application         ← ✅ Complete
Phase 5: Multi-Profile & Voice      ← ✅ Complete
```

---

## Phase 0: Research Gap Fill (Complete the Foundation)

**Goal**: Fill the 3 gaps left by rate-limited searches. Make the research foundation airtight.

**Tasks**:
1. Search for more GitHub repos: behavioral modeling, user profiling, time-series pattern recognition, food recommendation systems
2. Deepen Indian regional food behavior research: state-wise dietary patterns, vegetarian/non-veg distribution, regional cuisine psychology
3. Find and analyze habit loop / behavioral change application papers: Charles Duhigg framework applied to food, nudge theory in food delivery, AI-driven behavioral interventions
4. Search for Indian food delivery data science projects: Swiggy/Zomato analysis repos, Kaggle datasets, academic papers
5. Update `02-technical-tools-repos.md` with new findings
6. Create `03-behavioral-change-models.md` with habit loop, nudge theory, and behavioral intervention research
7. Push all updates to GitHub

**Deliverables**:
- Updated `02-technical-tools-repos.md` with more repos and datasets
- New `03-behavioral-change-models.md` — behavioral change frameworks for food
- Updated `README.md` if needed
- Git commit + push

**Success Criteria**:
- At least 10 relevant GitHub repos identified and analyzed
- Indian regional food behavior covered for all major regions
- At least 3 behavioral change frameworks documented with application to food
- All gaps from rate limiting filled

---

## Phase 1: Food DNA Taxonomy Design

**Goal**: Design the complete Food DNA taxonomy — what dimensions exist, how they're measured, how they combine into a behavioral profile.

**Tasks**:
1. Define Food DNA dimensions based on psychological research:
   - Cultural Identity (religion, vegetarianism, regional)
   - Cuisine Preferences (cuisine types, flavor profiles, spice tolerance)
   - Temporal Patterns (meal timing, ordering frequency, day-of-week)
   - Price Psychology (budget range, coupon sensitivity, value perception)
   - Health Orientation (dietary goals, calorie awareness, restriction compliance)
   - Social Dynamics (solo vs family vs group, hospitality patterns)
   - Emotional Patterns (comfort food, celebration food, stress eating)
   - Life Stage (student, professional, parent, elderly)
2. Design scoring system for each dimension
3. Design how dimensions combine into a "Food DNA Profile"
4. Design how Food DNA evolves over time (learning rate, adaptation)
5. Map MCP signals to each dimension (which tool provides which data)
6. Create sample Food DNA profiles for different Indian user archetypes
7. Document everything in `design/01-food-dna-taxonomy.md`
8. Push to GitHub

**Deliverables**:
- `design/01-food-dna-taxonomy.md` — Complete taxonomy with dimensions, scoring, and examples
- Sample profiles: South Indian professional, North Indian family, Bengali student, Gujarati elderly
- Git commit + push

**Success Criteria**:
- At least 8 well-defined dimensions with clear measurement criteria
- Each dimension mapped to specific MCP tool signals
- At least 4 sample user profiles with realistic Food DNA scores
- Taxonomy validated against psychological frameworks

---

## Phase 2: Recommendation Engine Prototype

**Goal**: Build a working prototype of the recommendation engine that uses Food DNA to generate personalized suggestions.

**Tasks**:
1. Design the recommendation algorithm:
   - Content-based filtering using IFCT 2017 food attributes
   - Collaborative filtering using behavioral similarity
   - Hybrid approach combining both with Food DNA weights
2. Design the data pipeline:
   - MCP signal ingestion → feature extraction → Food DNA calculation → recommendation
3. Design the prediction models:
   - Next order prediction (when)
   - Cuisine prediction (what type)
   - Restaurant prediction (where)
   - Meal planning (weekly pattern)
4. Design the nudge engine:
   - When to suggest (timing)
   - What to suggest (content)
   - How to suggest (tone, framing)
   - When NOT to suggest (respect autonomy)
5. Create technical specification in `technical/01-recommendation-engine.md`
6. Push to GitHub

**Deliverables**:
- `technical/01-recommendation-engine.md` — Algorithm design, data pipeline, prediction models
- Recommendation flow diagrams
- Nudge decision tree
- Git commit + push

**Success Criteria**:
- Clear algorithm design with mathematical formulation
- Data pipeline mapped from MCP signals to recommendations
- Nudge engine respects psychological principles (SDT, stages of change)
- At least 3 recommendation types designed (proactive, reactive, contextual)

---

## Phase 3: MCP Integration & Agent Build

**Goal**: Build the actual agent that connects to Swiggy's MCP servers and implements the Food DNA system.

**Tasks**:
1. Set up MCP client using Python SDK
2. Implement MCP tool calls for all 3 servers:
   - Food: `search_restaurants`, `get_restaurant_menu`, `search_menu`, `your_go_to_items`, `get_food_orders`
   - Instamart: `search_products`, `your_go_to_items`, `get_orders`
   - Dineout: `search_restaurants_dineout`, `get_booking_status`
3. Implement behavioral signal extraction:
   - Parse `your_go_to_items` for grocery patterns
   - Parse `get_food_orders` for restaurant patterns
   - Parse `get_booking_status` for dining patterns
4. Implement Food DNA calculator:
   - Score each dimension from MCP signals
   - Generate Food DNA profile
   - Update profile with each new signal
5. Implement recommendation engine:
   - Generate personalized recommendations based on Food DNA
   - Handle voice vs chat response shaping
   - Handle error recovery (cart expired, item unavailable)
6. Implement nudge engine:
   - Proactive suggestions (time-based, context-based)
   - Respect user autonomy (don't over-recommend)
7. Create agent implementation in `technical/02-agent-implementation.md`
8. Push to GitHub

**Deliverables**:
- `technical/02-agent-implementation.md` — Code architecture, MCP integration, agent logic
- Working agent code (Python)
- Git commit + push

**Success Criteria**:
- Agent connects to all 3 MCP servers
- Behavioral signals extracted from MCP responses
- Food DNA profile generated from real data
- Recommendations personalized to Food DNA
- Voice and chat response shaping implemented

---

## Phase 4: Demo & Application

**Goal**: Create a compelling demo video and apply to Swiggy Builders Club.

**Tasks**:
1. Create demo scenarios:
   - Scenario 1: Voice reorder — "Order my usual" → behavioral lookup → confirm → order
   - Scenario 2: Proactive suggestion — "It's Friday, your usual biryani?"
   - Scenario 3: Cross-server — "Plan my evening" → Dineout + Food + Instamart
   - Scenario 4: Error recovery — Restaurant closed → suggest alternative
   - Scenario 5: Festival awareness — "Diwali is tomorrow, order sweets?"
2. Record demo video (3 minutes max)
3. Write application:
   - Project description
   - Technical approach
   - Why this matters for Swiggy
   - Demo video link
4. Apply at https://mcp.swiggy.com/builders/access/
5. Document everything in `design/02-demo-and-application.md`
6. Push to GitHub

**Deliverables**:
- `design/02-demo-and-application.md` — Demo scenarios, application text, video link
- Demo video (3 min)
- Application submitted
- Git commit + push

**Success Criteria**:
- Demo shows at least 3 different capabilities
- Demo handles at least 1 error case
- Application includes working demo video
- Application submitted to Swiggy Builders Club

---

## Phase Execution Rules

1. **One phase at a time** — Complete all tasks in current phase before starting next
2. **Push after each phase** — Every phase ends with git commit + push
3. **Quality over speed** — Better to spend 2 days on a solid taxonomy than rush through
4. **Document everything** — Every decision, every finding, every design choice gets written down
5. **Psychology-first** — Every design decision should be grounded in psychological theory, not just "it works"

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|-------------|
| Phase 0: Research Gap Fill | 1-2 days | None |
| Phase 1: Food DNA Taxonomy | 2-3 days | Phase 0 complete |
| Phase 2: Recommendation Engine | 2-3 days | Phase 1 complete |
| Phase 3: MCP Integration | 3-5 days | Phase 2 complete |
| Phase 4: Demo & Application | 2-3 days | Phase 3 complete |
| **Total** | **10-16 days** | |

---

## Current Status

- [x] Initial research (rate-limited but solid foundation)
- [x] Project folder created
- [x] Implementation plan written
- [x] Phase 0: Research Gap Fill ✅ (6 research files complete, pushed to GitHub)
- [x] Phase 1: Food DNA Taxonomy Design ✅ (design/01-food-dna-taxonomy.md — 1101 lines, 10 dimensions, 4 profiles)
- [x] Phase 2: Recommendation Engine Prototype ✅ (technical/01-recommendation-engine.md — 1060 lines, 3 engines, nudge, MCP specs)
- [x] Phase 3: MCP Integration & Agent Build ✅ (src/ — 11 Python files, 3566 lines + technical/02-agent-implementation.md)
- [x] Phase 4: Demo & Application ✅ (design/02-demo-and-application.md + demo.py — 5 scenarios, application text, recording guide)
- [x] Phase 5: Multi-Profile, Chat Enhancement, Voice Agent ✅
  - [x] 5A: Multi-Profile System — 5 profile JSONs, profile selector UI, profile-aware demo
  - [x] 5B: Chat Enhancement — Rich cards, quick actions, context-aware suggestions, dark/light mode
  - [x] 5C: Voice Agent — TTS (Listen button) + STT (mic input), browser-native, zero server cost
  - [x] Deployed to Railway + pushed to both repos (AI-video-editing + swigy-builders)
