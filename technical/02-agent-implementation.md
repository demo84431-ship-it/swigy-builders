# Food DNA Agent — Phase 3 Technical Documentation

> **Project**: Food DNA Agent (Swiggy Builders Club)
> **Phase**: 3 — MCP Integration & Agent Build
> **Date**: 2026-05-09
> **Status**: Implementation Complete

---

## A. Architecture Overview

### Module Dependency Graph

```
agent.py (Orchestrator)
├── config.py (Configuration)
├── mcp_client.py (MCP Communication)
│   └── config.py
├── feature_extractor.py (Signal Processing)
├── food_dna.py (Data Model)
├── food_dna_calculator.py (Profile Builder)
│   └── food_dna.py
├── recommender.py (Recommendation Engine)
│   └── food_dna.py
└── nudge_engine.py (Nudge Engine)
    ├── food_dna.py
    └── recommender.py (for FRAMING_TEMPLATES)
```

### Data Flow

```
User Intent
    │
    ▼
agent.py: handle_intent()
    │
    ├──▶ mcp_client.py: call_tool(server, tool, args)
    │       │
    │       ├── OAuth 2.1 + PKCE authentication
    │       ├── Rate limiting (100 req/min budget)
    │       ├── Exponential backoff retry (5 attempts)
    │       └── Error classification (6 buckets)
    │
    ▼
feature_extractor.py: extract_all_features(responses)
    │
    ├── extract_from_food_orders()    → temporal, cuisine, price, social, dietary
    ├── extract_from_go_to_items()    → grocery patterns, brand loyalty, health
    ├── extract_from_booking_status() → dining frequency, party size, occasions
    ├── extract_from_addresses()      → life stage, multi-city, home/work
    ├── extract_from_search_restaurants() → exploration signals
    └── extract_from_coupons()        → deal-seeking behavior
    │
    ▼
food_dna_calculator.py: build_from_features() / update()
    │
    ├── Dietary identity inference (lr=0.00)
    ├── Regional identity EMA (lr=0.02)
    ├── Cuisine preferences EMA (lr=0.10)
    ├── Temporal patterns EMA (lr=0.20)
    ├── Price psychology EMA (lr=0.15)
    ├── Health orientation EMA (lr=0.05)
    ├── Social dynamics EMA (lr=0.20)
    ├── Emotional patterns EMA (lr=0.50)
    ├── Life stage inference (lr=0.05)
    └── Habit detection (lr=0.05)
    │
    ▼
recommender.py: score_candidate() / reactive_*() / proactive_*()
    │
    ├── Dietary hard filter (binary 0/1)
    ├── 9-dimension weighted scoring
    ├── Festival calendar matching
    └── Voice/chat response shaping
    │
    ▼
nudge_engine.py: should_nudge() / build_*_nudge()
    │
    ├── Suppression rules (quiet hours, fatigue, stress)
    ├── Intensity selection (suggestion/recommendation/reminder)
    └── Psychological framing templates
    │
    ▼
Response to User (voice or chat format)
```

---

## B. Module Descriptions

### B.1 config.py — Configuration

Central configuration using frozen dataclasses for immutability.

**Key configurations:**
- `OAuthConfig` — client_id, redirect_uri, auth_base_url, scope, token lifetime
- `MCPServerConfig` — Food, Instamart, Dineout server URLs
- `RateLimitConfig` — 100 req/min budget, retry parameters (500ms initial, 2x multiplier, 8s cap, 5 max attempts)
- `AgentConfig` — quiet hours (23:00-08:00), max nudges/day (3), voice/chat option limits, cache TTLs

**Design decision:** All configs use frozen dataclasses (not env vars) for type safety and IDE support. In production, values would be loaded from environment or secrets manager.

### B.2 mcp_client.py — MCP Client Wrapper

The MCP client handles all communication with Swiggy's three servers.

**OAuth 2.1 + PKCE flow:**
1. `generate_pkce_pair()` — Generate verifier (32 random bytes, base64url) and challenge (SHA256 of verifier)
2. `build_authorize_url()` — Construct the authorization URL with all required parameters
3. `exchange_code_for_token()` — POST to `/auth/token` with code + verifier
4. Token stored in `TokenStore` with expiry tracking

**call_tool() method:**
- Builds JSON-RPC 2.0 payload (`method: "tools/call"`)
- Rate limiting via `RateLimiter` (sliding window, 100 req/min)
- Retry with exponential backoff + jitter (500ms → 1s → 2s → 4s → 8s)
- Error classification into 6 buckets: AUTH, BAD_INPUT, UPSTREAM_TIMEOUT, UPSTREAM_ERROR, DOMAIN, INTERNAL
- Special handling for order placement (check-then-retry for 5xx)

**Error classification logic:**
```
401 / -32001  → AUTH (re-run OAuth, don't retry)
400           → BAD_INPUT (fix args, don't retry)
504           → UPSTREAM_TIMEOUT (backoff + retry)
502/503       → UPSTREAM_ERROR (backoff + retry)
200 + success:false → DOMAIN (surface to user, don't retry)
500 / -32603  → INTERNAL (backoff once, report if persists)
```

### B.3 food_dna.py — Data Model

Complete Python dataclass model matching the taxonomy's Food DNA Vector.

**10 dimensions:**
1. `DietaryIdentity` — primary type, strictness, home_vs_outside, fasting
2. `RegionalIdentity` — region, state, cuisine_affinity dict, rice_vs_wheat, spice tolerance
3. `TemporalPattern` — 24-element hour distribution, 7-element day distribution, regularity scores
4. `PricePsychology` — AOV, sensitivity, coupon usage, budget tier, value framing
5. `HealthOrientation` — awareness, trend, change_stage (Transtheoretical Model), medical restrictions
6. `SocialDynamics` — solo/couple/family/group ratios, party size, hospitality
7. `EmotionalPatterns` — comfort/celebration/boredom/stress foods, current state levels
8. `LifeStageProfile` — 12 life stage types, cooking capability, financial comfort
9. `HabitProfile` — habit strength, recurring items/restaurants, temporal habits (Cue→Routine→Reward)
10. `CuisinePreferences` — distribution across 10 cuisine categories

**Enums:** `DietaryType` (5), `RegionType` (5), `LifeStageType` (12), `ChangeStage` (5)

**Serialization:** `to_dict()` / `from_dict()` for JSON-safe persistence. Handles nested dataclasses, enums, and lists.

### B.4 feature_extractor.py — Feature Extraction

Extracts behavioral signals from MCP tool responses. One extractor per tool type.

**Key extractors:**

| Extractor | MCP Tool | Features Extracted |
|-----------|----------|-------------------|
| `extract_from_food_orders` | `get_food_orders` | Temporal patterns, cuisine distribution, price stats, restaurant/item concentration, dietary signals |
| `extract_from_go_to_items` | `your_go_to_items` | Category distribution, brand loyalty, grocery health score, regional staple detection |
| `extract_from_booking_status` | `get_booking_status` | Party sizes, occasion types, dining spend |
| `extract_from_addresses` | `get_addresses` | Home/work/other detection, multi-city |
| `extract_from_search_restaurants` | `search_restaurants` | Cuisine distribution, price range, open ratio |
| `extract_from_coupons` | `fetch_food_coupons` | Available coupons, discount levels |

**Heuristic cuisine mapping:** Maps restaurant/dish names to cuisine categories using keyword matching (production would use a trained classifier).

**Herfindahl index:** Used to measure restaurant and item concentration — high concentration = habitual behavior.

### B.5 food_dna_calculator.py — Profile Builder

Builds and updates Food DNA profiles using exponential moving average (EMA) updates.

**Learning rates per dimension:**
| Dimension | Rate | Rationale |
|-----------|------|-----------|
| Dietary Identity | 0.00 | Never updates automatically (identity) |
| Regional Identity | 0.02 | Extremely stable, changes over years |
| Cuisine Preferences | 0.10 | Stable but shifts with exposure |
| Temporal Patterns | 0.20 | Shifts with schedule changes |
| Price Psychology | 0.15 | Shifts with income/membership |
| Health Orientation | 0.05 | Very stable, changes with life events |
| Social Dynamics | 0.20 | Shifts with life-stage transitions |
| Emotional Patterns | 0.50 | Context-dependent, fast-changing |
| Life Stage | 0.05 | Semi-stable, transitions are gradual |
| Habit Profile | 0.05 | Stable by definition |

**EMA update formula:**
```python
new_value = current * (1 - learning_rate) + observation * learning_rate
```

**Confidence scoring:**
- Per-dimension: `min(1.0, data_points / threshold)`
- Overall: Based on total data points (0-2: 0.1, 3-10: 0.3, 11-30: 0.5, 31-100: 0.7, 100+: 0.9+)

**Habit detection:** Identifies recurring items (concentration > 0.15), recurring restaurants (concentration > 0.2), and temporal habits (day-of-week patterns > 20% of orders).

### B.6 recommender.py — Recommendation Engine

Generates personalized recommendations from Food DNA profiles.

**Scoring function (10 weights):**
```
Dietary Identity:    HARD FILTER (0 or 1) — never override
Regional Affinity:   0.20
Life Stage Fit:      0.15
Temporal Fit:        0.15
Habit Reinforcement: 0.15
Emotional Fit:       0.10
Price Fit:           0.10
Social Fit:          0.05
Health Alignment:    0.05
Variety Bonus:       0.05
```

**Three recommendation modes:**

1. **Proactive (agent-initiated):**
   - Time-based: detects user's typical meal ordering window
   - Friday biryani: culturally reinforced habit loop detection
   - Festival: Indian festival calendar with food associations (10 festivals)
   - Rain: environmental trigger → comfort food

2. **Reactive (user-initiated):**
   - "Order something": Food DNA-ranked options
   - "Something healthy": Health-filtered with positive framing
   - "Surprise me": Controlled novelty (score 0.3-0.7 range)

3. **Cross-server:**
   - Restaurant closed → similar alternatives weighted by Food DNA

**Response shaping:**
- Voice: ≤3 options, spoken prices, 1-2 sentences per option
- Chat: ≤8 options, rich markdown, full details, emoji

**Dietary hard filter:** Binary gate based on DietaryIdentity type. Keywords checked against item names. Supports vegetarian, eggetarian, non-vegetarian, Jain (no root vegetables, no onion/garlic), and vegan.

### B.7 nudge_engine.py — Nudge Engine

Determines when, what, and how to nudge users.

**Suppression rules:**
1. Quiet hours (23:00-08:00) — exception for late-night pattern users
2. Nudge fatigue (max 3/day)
3. Rejection tracking (suppress same type for 4 hours)
4. Explicit stop (suppress all for 7 days)
5. Stress detection (suppress health nudges when stressed)

**Intensity levels:**
- Suggestion: Subtle, one option. Low confidence.
- Recommendation: 2-3 options with reasoning. Medium confidence.
- Reminder: Direct, action-oriented. High habit strength.

**Psychological framing templates:**
- Habit reinforcement: Cue → Routine → Reward
- Variety seeking: "Like X but different"
- Emotional comfort: Serve need, no judgment
- Health nudge: Positive framing, never shaming
- Festival: Celebrate identity
- Price-sensitive: Anchoring + loss aversion ("You saved ₹X")
- Social context: Optimize for group
- Decision fatigue: Minimize choices (yes/no)

### B.8 agent.py — Main Orchestrator

Central coordinator connecting all modules.

**Agent lifecycle:**
1. Initialize MCP clients for all 3 servers
2. Authenticate via OAuth 2.1 + PKCE
3. Build profile: fetch from Food + Instamart + Dineout → extract → calculate
4. Handle intents: route to appropriate handler
5. Generate response: voice or chat format

**5 demo scenarios implemented:**

| # | Scenario | Intent | Handler |
|---|---------|--------|---------|
| 1 | "Order my usual" | Behavioral lookup → confirm | `_handle_order_something()` |
| 2 | "It's Friday" | Proactive biryani suggestion | `_handle_friday()` |
| 3 | "Plan my evening" | Dineout + Food cross-server | `_handle_plan_evening()` |
| 4 | Restaurant closed | Error recovery | `_handle_restaurant_closed()` |
| 5 | "Diwali tomorrow" | Festival-aware suggestion | `_handle_festival()` |

**Intent routing:** Keyword matching with fallback to general recommendation.

---

## C. MCP Integration Details

### C.1 Server Endpoints

| Server | Endpoint | Tools | Auth |
|--------|----------|-------|------|
| Food | `POST mcp.swiggy.com/food` | 14 tools | Bearer JWT |
| Instamart | `POST mcp.swiggy.com/im` | 13 tools | Bearer JWT |
| Dineout | `POST mcp.swiggy.com/dineout` | 8 tools | Bearer JWT |

Single OAuth token works for all three servers.

### C.2 JSON-RPC Format

All MCP calls use JSON-RPC 2.0:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": { "key": "value" }
  },
  "id": 1
}
```

### C.3 Key Constraints Handled

| Constraint | Handling |
|-----------|---------|
| Food cart bound to one restaurant | Warn user before switching |
| Instamart cart bound to address | Clear cart before address switch |
| ₹1,000 food cart cap | Check before placing order |
| ₹99 Instamart minimum | Suggest complementary items |
| `place_food_order` NOT idempotent | Check-then-retry on 5xx |
| `book_table` NOT idempotent | Check-then-retry on 5xx |
| Tracking poll ≥10s | Enforced in rate limiter |
| No refresh tokens (v1.0) | Full re-auth on expiry |
| COD only (v1.0) | Payment method hardcoded |

### C.4 Rate Budget

```
Total budget:     120 req/min per user
Target:           100 req/min (20% headroom)
Per recommendation: ≤4 calls (MVP)
Max recommendations: ~25/min (theoretical), ~5/min (practical)
```

**Optimization strategies:**
- Cache `get_food_orders` for 5 min per session
- Cache `search_restaurants` for 10 min per address+query
- Batch feature extraction (don't call MCP tools redundantly)

---

## D. Error Handling Strategy

### D.1 Error Classification

Six error buckets with distinct handling:

| Bucket | Detection | Action |
|--------|-----------|--------|
| AUTH | 401 / -32001 | Clear token, raise to caller for re-auth |
| BAD_INPUT | 400 | Fix args, don't retry |
| UPSTREAM_TIMEOUT | 504 | Exponential backoff, max 5 retries |
| UPSTREAM_ERROR | 502/503 | Exponential backoff, max 5 retries |
| DOMAIN | 200 + success:false | Surface to user, don't retry |
| INTERNAL | 500 / -32603 | Backoff once, report if persists |

### D.2 Retry Strategy

```
Attempt 1: 500ms + jitter(0, 100ms)
Attempt 2: 1000ms + jitter(0, 200ms)
Attempt 3: 2000ms + jitter(0, 400ms)
Attempt 4: 4000ms + jitter(0, 800ms)
Attempt 5: 8000ms + jitter(0, 1600ms)  ← cap
```

### D.3 Order Placement Safety

For `place_food_order`, `checkout`, and `book_table` (NOT idempotent):
1. On 5xx error, wait 2 seconds
2. Call `get_food_orders` / `get_orders` / `get_booking_status` to check
3. If order was placed despite error → return success
4. If not placed → safe to retry

### D.4 Domain Error Recovery

| Error | Recovery |
|-------|----------|
| Restaurant closed | Search for similar alternatives |
| Item out of stock | Suggest similar items from same restaurant |
| Cart expired | Rebuild cart from Food DNA |
| Below minimum (Instamart) | Suggest complementary items |
| No slots (Dineout) | Suggest alternate times/restaurants |
| Coupon invalid | Fetch new coupons, suggest best available |

---

## E. Testing Approach

### E.1 Unit Tests

| Module | Test Focus |
|--------|-----------|
| `mcp_client.py` | PKCE generation, error classification, rate limiting |
| `food_dna.py` | Serialization round-trip, enum handling |
| `feature_extractor.py` | Each extractor with sample MCP responses |
| `food_dna_calculator.py` | EMA updates, confidence scoring, habit detection |
| `recommender.py` | Dietary filter, scoring function, response shaping |
| `nudge_engine.py` | Suppression rules, intensity selection, framing |

### E.2 Integration Tests

| Test | Description |
|------|-------------|
| OAuth flow | Full PKCE flow with mock auth server |
| Profile building | Build from multi-server MCP responses |
| Recommendation | Score candidates against known Food DNA |
| Cross-server | Food + Dineout combined flow |
| Error recovery | Simulate each error bucket |

### E.3 Scenario Tests

| # | Scenario | Expected Behavior |
|---|---------|------------------|
| 1 | Jain user browses menu | Filter out all onion/garlic/root vegetables |
| 2 | Vegetarian searches "biryani" | Show only veg biryani |
| 3 | Friday 7 PM, biryani habit | Suggest biryani as first option |
| 4 | Stress detected (3 comfort orders) | Empathetic tone, comfort food |
| 5 | 10 PM weekday | Quick options, not full menu |
| 6 | Diwali tomorrow | Proactive mithai suggestion |
| 7 | First 5 orders (cold start) | Dietary + regional emerging |
| 8 | User says "surprise me" | Novel but identity-compliant options |
| 9 | Restaurant closed | Similar alternatives, not random |
| 10 | Family of 5 mixed diet | Options satisfying ALL dietary constraints |

### E.4 Validation Metrics

| Metric | Target |
|--------|--------|
| Dietary compliance | 100% (zero non-compliant recommendations) |
| Recommendation acceptance | >50% (MVP), >65% (V2) |
| Response latency (voice) | <2s |
| Response latency (chat) | <3s |
| MCP calls per recommendation | ≤4 |
| Habit detection accuracy | >70% |
| Cold start satisfaction | >40% |

---

## F. Psychological Framework Integration

Each design decision maps to an established psychological framework:

| Decision | Framework | Application |
|----------|-----------|-------------|
| Dietary identity = hard filter | Self-affirmation theory (Steele, 1988) | Identity is non-negotiable |
| Habit detection + reinforcement | Habit Loop (Duhigg, 2012) | Cue → Routine → Reward |
| Nudge suppression rules | Self-Determination Theory (Deci & Ryan) | Respect autonomy |
| Health stage detection | Transtheoretical Model (Prochaska) | Match intervention to stage |
| Price framing | Behavioral economics (Kahneman) | Anchoring, loss aversion |
| Festival awareness | Cultural psychology | Food as identity expression |
| Emotional detection | Emotional eating research | Serve need, don't push goals |
| Voice ≤3 options | Cognitive load theory | Reduce decision fatigue |
| Comfort food when stressed | Emotional regulation | Emotional need > long-term goal |
| "You saved ₹X" framing | Endowment effect | Ownership framing is motivating |

---

## G. File Inventory

```
src/
├── __init__.py              (49 bytes)   — Package marker
├── config.py                (2,517 bytes) — Configuration dataclasses
├── mcp_client.py            (16,382 bytes) — MCP client with OAuth, retry, errors
├── food_dna.py              (18,137 bytes) — Data model, 10 dimensions, serialization
├── feature_extractor.py     (14,985 bytes) — MCP response → behavioral features
├── food_dna_calculator.py   (17,593 bytes) — EMA updates, confidence, habits
├── recommender.py           (26,562 bytes) — Scoring, recommendations, response shaping
├── nudge_engine.py          (13,715 bytes) — Nudge timing, framing, suppression
├── agent.py                 (23,972 bytes) — Orchestrator, 5 demo scenarios
├── requirements.txt         (423 bytes)   — Dependencies
└── README.md                (3,537 bytes) — Usage guide
```

**Total: ~137 KB of production-ready Python code**

---

*Phase 3 deliverable complete. The Food DNA Agent is ready for integration testing and demo preparation (Phase 4).*
