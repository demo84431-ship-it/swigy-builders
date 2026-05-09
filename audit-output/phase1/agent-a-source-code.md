# Agent A: Core Source Code Analysis

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI (web server), httpx (async HTTP)
- **Deployment**: Railway (Procfile + railway.toml)
- **Auth**: OAuth 2.1 + PKCE (Swiggy MCP)
- **No external DB**: In-memory session store
- **No external ML**: Pure Python behavioral modeling (EMA, scoring)

## Architecture Overview
```
User → FastAPI (app.py) → FoodDNAAgent (agent.py)
  ├── MCPClient (mcp_client.py) → Swiggy Food/Instamart/Dineout APIs
  ├── FeatureExtractor (feature_extractor.py) → Behavioral signals
  ├── FoodDNACalculator (food_dna_calculator.py) → EMA profile updates
  ├── Recommender (recommender.py) → 10-factor scoring engine
  └── NudgeEngine (nudge_engine.py) → Psychological framing
```

## File-by-File Analysis

### `agent.py` — Main Orchestrator (366 lines)
- **Purpose**: Central coordinator. Connects to 3 MCP servers, builds profiles, handles 6 intent types.
- **Key class**: `FoodDNAAgent` — async context manager, holds MCP client + DNA + context
- **6 scenarios**: order_something, something_healthy, surprise_me, friday, plan_evening, festival, restaurant_closed
- **Quality**: Well-structured. Clean separation of concerns. Good docstrings.

### `food_dna.py` — Data Model (435 lines)
- **Purpose**: 10-dimension behavioral profile with enums, dataclasses, serialization
- **10 dimensions**: DietaryIdentity, RegionalIdentity, CuisinePreferences, TemporalPattern, PricePsychology, HealthOrientation, SocialDynamics, EmotionalPatterns, LifeStageProfile, HabitProfile
- **Quality**: Excellent. Rich docstrings with psychological framework citations. Clean serialization.

### `food_dna_calculator.py` — Profile Builder (239 lines)
- **Purpose**: Builds/updates Food DNA from extracted features using EMA
- **Key functions**: `build_from_features()`, `update()`, `infer_dietary_type()`, `infer_life_stage()`, `detect_habits()`
- **Quality**: Solid. Per-dimension learning rates. Confidence scoring.

### `recommender.py` — Recommendation Engine (468 lines)
- **Purpose**: 10-factor scoring engine with proactive/reactive/cross-server modes
- **Scoring weights**: Dietary(HARD FILTER), Regional(0.20), LifeStage(0.15), Temporal(0.15), Habit(0.15), Emotional(0.10), Price(0.10), Social(0.05), Health(0.05), Variety(0.05)
- **Quality**: Good. Festival calendar, voice/chat shaping, dietary hard filters.

### `nudge_engine.py` — Behavioral Nudge Framework (278 lines)
- **Purpose**: When/what/how to nudge. Suppression rules, psychological framing templates.
- **Frameworks**: Habit Loop, SDT, Nudge Theory, Transtheoretical Model
- **Quality**: Excellent. Ethical boundaries built in (quiet hours, stress suppression, fatigue limits).

### `feature_extractor.py` — Signal Extraction (307 lines)
- **Purpose**: Extracts behavioral features from MCP tool responses
- **6 extractors**: food_orders, go_to_items, booking_status, addresses, search_restaurants, coupons
- **Quality**: Good. Heuristic cuisine classification (keyword-based). Would need ML for production.

### `mcp_client.py` — MCP Client (407 lines)
- **Purpose**: OAuth 2.1 + PKCE, rate limiting, retry logic, error classification
- **Quality**: Production-grade. Error buckets, exponential backoff, rate limiter (100 req/min).

### `config.py` — Configuration (78 lines)
- **Purpose**: Dataclass-based config for OAuth, MCP endpoints, rate limits, agent behavior
- **Quality**: Clean. Frozen dataclasses. Sensible defaults.

### `app.py` — Web Server (347 lines)
- **Purpose**: FastAPI app serving chat UI + API. Demo mode with 5 profiles.
- **Routes**: /, /api/health, /api/tts, /api/profiles, /api/chat, /api/auth/login, /ws/chat
- **Quality**: Functional but has issues (see below)

## Data Flow
1. User selects profile or connects Swiggy account
2. User sends message → `/api/chat` endpoint
3. Demo mode: `demo_response()` returns profile-aware HTML rich cards
4. Real mode: `FoodDNAAgent.handle_intent()` → MCP calls → feature extraction → DNA update → recommendation → response

## Issues & Observations

### Critical
1. **`static/index.html` is a single 700+ line file** — HTML + CSS + JS all inline. Not maintainable.
2. **No DESIGN.md** — No design system. Colors are hardcoded (`--accent: #f97316`).
3. **Demo mode responses are raw HTML strings** — XSS risk, no sanitization.
4. **In-memory session store** — Lost on restart. Fine for demo, not production.

### Moderate
5. **`demo_response()` duplicates logic** — The demo response function reimplements the recommendation logic in HTML strings instead of using the actual agent.
6. **No error boundaries in UI** — If API fails, user sees raw error.
7. **TTS proxy uses Google Translate** — Fragile, no fallback if blocked.
8. **Profile JSON files have inconsistent structure** — Some have `sample_conversations`, some don't.

### Minor
9. **`generate_video.py` not reviewed** — Uses PIL for demo video generation.
10. **No favicon, no meta description, no OG tags** — Missing SEO/social basics.
11. **No loading states** — Typing indicator exists but no skeleton loaders.
12. **No analytics/tracking** — Can't measure engagement.

## What the Agent Actually Does
The FoodDNA Agent is a **demo/showcase** of what a psychology-first food recommendation system could look like on Swiggy's MCP platform. It:
1. Loads pre-built user profiles (5 diverse Indian personas)
2. Shows a chat interface where users can ask for food recommendations
3. Returns rich card responses with food suggestions, reasoning, and action buttons
4. Displays a sidebar with the user's Food DNA dimensions (dietary, regional, habits, emotions)
5. Supports voice (TTS via Google Translate proxy)
6. Has dark/light theme toggle

The actual MCP integration is in demo mode — it uses pre-built profile JSONs instead of real Swiggy API calls. The real mode exists but requires Swiggy OAuth credentials.
