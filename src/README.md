# Food DNA Agent — Source Code

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                         │
│              Voice (≤3 options) / Chat (≤8 options)             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      agent.py (Orchestrator)                    │
│  Intent routing → MCP calls → Feature extraction → Response     │
└──────────┬────────────┬────────────┬────────────┬──────────────┘
           │            │            │            │
     ┌─────▼────┐ ┌─────▼────┐ ┌────▼─────┐ ┌───▼────────┐
     │ mcp_     │ │ feature_ │ │ food_dna_│ │ recommender│
     │ client   │ │ extractor│ │ calc     │ │ + nudge    │
     └─────┬────┘ └──────────┘ └──────────┘ └────────────┘
           │
     ┌─────▼────────────────────────────────────┐
     │  Swiggy MCP Servers (Food/Instamart/     │
     │  Dineout) — OAuth 2.1 + PKCE             │
     └──────────────────────────────────────────┘
```

## Modules

| File | Purpose |
|------|---------|
| `config.py` | MCP endpoints, OAuth config, rate limits, agent tuning |
| `mcp_client.py` | OAuth 2.1 + PKCE, retry logic, error classification, rate limiting |
| `food_dna.py` | Data model — 10 dimensions, enums, serialization |
| `feature_extractor.py` | Parse MCP responses into behavioral features |
| `food_dna_calculator.py` | EMA updates, confidence scoring, habit detection |
| `recommender.py` | Scoring, proactive/reactive recommendations, voice/chat shaping |
| `nudge_engine.py` | When/what/how to nudge, suppression rules, psychological framing |
| `agent.py` | Main orchestrator, 5 demo scenarios, intent routing |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run demo (uses mock token)
python -m src.agent

# In production:
# 1. Set your OAuth client_id in config.py
# 2. Implement the OAuth callback to receive the authorization code
# 3. Call agent.authenticate(code, verifier)
# 4. Call agent.build_profile() to build Food DNA from MCP signals
# 5. Call agent.handle_intent("order something") for recommendations
```

## Configuration

Edit `config.py` to set:
- `OAuthConfig.client_id` — Your Swiggy Builders Club client ID
- `OAuthConfig.redirect_uri` — Your OAuth callback URL
- `RateLimitConfig` — Adjust rate limits if needed
- `AgentConfig` — Tune nudge timing, response options, cache TTLs

## Demo Scenarios

The agent handles 5 key scenarios:

1. **"Order my usual"** → Behavioral lookup → confirm → order
2. **"It's Friday"** → Proactive biryani suggestion (habit loop detection)
3. **"Plan my evening"** → Dineout + Food cross-server fusion
4. **Restaurant closed** → Error recovery with Food DNA-weighted alternatives
5. **"Diwali tomorrow"** → Festival-aware suggestion

## Key Design Decisions

- **Dietary identity is a hard filter** — never suggest non-veg to a vegetarian (self-affirmation theory)
- **EMA updates with per-dimension learning rates** — stable dimensions (dietary=0.00) vs fast-changing (emotional=0.50)
- **Voice gets 3 options, chat gets 8** — reduce cognitive load for voice users
- **Never push health on stressed users** — serve emotional needs first
- **Friday biryani is culturally reinforced** — one of the strongest Indian food habits
- **Quiet hours respect** — no nudges 11 PM–8 AM (unless late-night pattern detected)
