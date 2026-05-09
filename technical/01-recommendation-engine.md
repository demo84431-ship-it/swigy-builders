# Recommendation Engine — Technical Specification

> **Project**: Food DNA Agent (Swiggy Builders Club)
> **Phase**: 2 — Recommendation Engine Prototype
> **Date**: 2026-05-09
> **Status**: Design Complete

---

## A. Architecture Overview

### How the Recommendation Engine Fits Into Food DNA

The recommendation engine is the **intelligence layer** that sits between the Food DNA behavioral profile and the user-facing agent. It transforms raw psychological profiling into actionable, personalized food suggestions.

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                         │
│              Voice (≤3 options) / Chat (≤8 options)             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION ENGINE                        │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Proactive   │  │   Reactive   │  │  Cross-Server Fusion  │  │
│  │  Recommender │  │  Recommender │  │  Recommender          │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬────────────┘  │
│         │                │                      │               │
│         └────────────────┼──────────────────────┘               │
│                          │                                      │
│                          ▼                                      │
│                 ┌─────────────────┐                             │
│                 │  Nudge Engine   │                             │
│                 │  (when/how/what)│                             │
│                 └────────┬────────┘                             │
│                          │                                      │
│                          ▼                                      │
│                 ┌─────────────────┐                             │
│                 │ Response Shaper │                             │
│                 │ (voice vs chat) │                             │
│                 └─────────────────┘                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FOOD DNA PROFILE                            │
│  10 dimensions × continuous scores × confidence × temporal state│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FEATURE EXTRACTION PIPELINE                     │
│         MCP Signals → Behavioral Features → Scores              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MCP SIGNAL SOURCES                        │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │ Food Server │    │ Instamart  │    │  Dineout   │            │
│  │  14 tools   │    │  13 tools  │    │   8 tools  │            │
│  └────────────┘    └────────────┘    └────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Signal Ingestion**: MCP tool calls return raw data (orders, addresses, bookings, go-to items)
2. **Feature Extraction**: Raw responses are parsed into behavioral features (cuisine distribution, temporal patterns, price sensitivity)
3. **Food DNA Construction**: Features are scored across 10 dimensions with confidence weights
4. **Recommendation Generation**: Three engines (proactive, reactive, cross-server) query the Food DNA profile
5. **Nudge Decision**: Timing, framing, and intensity are determined by psychological rules
6. **Response Shaping**: Output is formatted for voice (3 options, spoken prices) or chat (8 options, widgets)

---

## B. Data Pipeline Design

### B.1 MCP Signal Ingestion

Each MCP tool maps to specific behavioral features. The pipeline ingests signals in priority order:

| Priority | MCP Tool | Server | Features Extracted | Update Frequency |
|----------|----------|--------|-------------------|-----------------|
| 1 | `get_food_orders` | Food | All 10 dimensions (primary source) | Every session |
| 2 | `your_go_to_items` | Instamart | Dietary identity, regional, habits | Every session |
| 3 | `get_booking_status` | Dineout | Social dynamics, price, temporal | Every session |
| 4 | `get_addresses` | Shared | Life stage, social, regional | On change |
| 5 | `search_restaurants` | Food | Cuisine prefs, price, health | Every search |
| 6 | `get_restaurant_menu` | Food | Exploration signals, price range | Every browse |
| 7 | `fetch_food_coupons` | Food | Price psychology (deal-seeking) | Every session |
| 8 | `search_products` | Instamart | Dietary, health, regional | Every search |
| 9 | `get_food_order_details` | Food | Item-level signals | Per order |
| 10 | `search_restaurants_dineout` | Dineout | Social, cuisine, price | Every search |

### B.2 Feature Extraction Logic

```python
def extract_features(mcp_response: dict, tool_name: str) -> dict:
    """Extract behavioral features from MCP tool response."""

    features = {}

    if tool_name == "get_food_orders":
        orders = mcp_response.get("orders", [])
        features["order_count_30d"] = len([o for o in orders if within_30d(o["timestamp"])])
        features["cuisine_distribution"] = compute_cuisine_dist(orders)
        features["hour_distribution"] = compute_hour_dist(orders)
        features["day_distribution"] = compute_day_dist(orders)
        features["avg_order_value"] = mean([o["total"] for o in orders])
        features["aov_std"] = stdev([o["total"] for o in orders])
        features["restaurant_concentration"] = compute_hhi(orders, key="restaurantId")
        features["item_concentration"] = compute_hhi(orders, key="itemName")
        features["comfort_food_ratio"] = count_comfort(orders) / len(orders)
        features["dietary_violations"] = detect_violations(orders)

    elif tool_name == "your_go_to_items":
        items = mcp_response.get("items", [])
        features["go_to_categories"] = categorize_items(items)
        features["regional_staples"] = detect_regional(items)
        features["brand_loyalty"] = compute_brand_concentration(items)
        features["grocery_health_score"] = score_grocery_health(items)

    elif tool_name == "get_booking_status":
        bookings = mcp_response.get("bookings", [])
        features["dining_frequency_30d"] = len(bookings)
        features["avg_party_size"] = mean([b["partySize"] for b in bookings])
        features["dining_price_range"] = compute_price_range(bookings)
        features["occasion_types"] = categorize_occasions(bookings)

    elif tool_name == "get_addresses":
        addresses = mcp_response.get("addresses", [])
        features["address_count"] = len(addresses)
        features["home_work_distance"] = compute_distance(addresses)
        features["multi_city"] = detect_multi_city(addresses)

    return features
```

### B.3 Food DNA Profile Construction

The profile is built incrementally. On first interaction, only dietary identity and regional identity are inferred (cold start). Each subsequent order adds signal.

```python
def build_food_dna(features: dict, existing_profile: FoodDNA) -> FoodDNA:
    """Update Food DNA with new features using exponential moving average."""

    profile = existing_profile or FoodDNA()

    # Dietary identity: set once, rarely changes
    if profile.data_points < 5:
        profile.dietary_identity = infer_dietary(features)

    # Regional identity: very slow update (lr=0.02)
    regional_obs = infer_regional(features)
    profile.regional_identity.cuisine_affinity = ema_update(
        profile.regional_identity.cuisine_affinity, regional_obs, lr=0.02
    )

    # Cuisine preferences: slow update (lr=0.10)
    profile.cuisine_preferences = ema_update(
        profile.cuisine_preferences, features["cuisine_distribution"], lr=0.10
    )

    # Temporal patterns: medium update (lr=0.20)
    profile.temporal_pattern.hour_distribution = ema_update(
        profile.temporal_pattern.hour_distribution, features["hour_distribution"], lr=0.20
    )

    # Price psychology: medium update (lr=0.15)
    profile.price_psychology.avg_order_value = ema_update_scalar(
        profile.price_psychology.avg_order_value, features["avg_order_value"], lr=0.15
    )

    # Emotional patterns: fast update (lr=0.50)
    profile.emotional_patterns = update_emotional_state(profile, features)

    # Habit profile: very slow update (lr=0.05)
    profile.habit_profile = update_habits(profile.habit_profile, features)

    # Meta
    profile.data_points += 1
    profile.confidence_score = min(1.0, profile.data_points / 50)
    profile.last_updated = now_iso()

    return profile
```

### B.4 Store Design

| Data | Storage | TTL | Rationale |
|------|---------|-----|-----------|
| Food DNA profile | Redis (hot) + PostgreSQL (cold) | Persistent | Core identity, survives restarts |
| 30-day order window | PostgreSQL | 90 days | Rolling window for pattern detection |
| Feature vectors | Redis | 30 days | Fast access for scoring |
| Recommendation cache | Redis | 15 min | Avoid re-scoring same context |
| Nudge state | Redis | 24 hours | Track what was nudged, avoid repetition |
| Festival calendar | In-memory | 1 year | Static data, refresh annually |
| Weather cache | Redis | 30 min | Context signal, refresh frequently |

**On-the-fly computation** (not stored):
- Recommendation scores (computed per request)
- Nudge decisions (computed per context)
- Response shaping (computed per channel)
- Anomaly detection (computed per session)

---

## C. Recommendation Algorithm Design

### C.1 Scoring Foundation

All recommendation types share a common scoring function based on the 10 Food DNA dimensions:

```python
def score_candidate(item, food_dna: FoodDNA, context: Context) -> float:
    """Score a food item/restaurant for recommendation."""

    # HARD FILTER: Dietary compliance (binary 0/1)
    if not satisfies_dietary(item, food_dna.dietary_identity):
        return 0.0

    score = 0.0

    # Regional affinity (0.20)
    score += food_dna.regional_identity.cuisine_affinity.get(item.cuisine, 0.1) * 0.20

    # Life-stage fit (0.15)
    score += life_stage_fit(item, food_dna.life_stage, context) * 0.15

    # Temporal appropriateness (0.15)
    score += temporal_fit(item, food_dna.temporal_pattern, context) * 0.15

    # Habit reinforcement (0.15)
    score += habit_fit(item, food_dna.habit_profile) * 0.15

    # Emotional fit (0.10)
    score += emotional_fit(item, food_dna.emotional_patterns, context) * 0.10

    # Price fit (0.10)
    score += price_fit(item, food_dna.price_psychology) * 0.10

    # Social fit (0.05)
    score += social_fit(item, food_dna.social_dynamics, context) * 0.05

    # Health alignment (0.05)
    score += health_fit(item, food_dna.health_orientation, context) * 0.05

    # Variety bonus (0.05)
    score += variety_bonus(item, food_dna.habit_profile) * 0.05

    return score
```

### C.2 Proactive Recommendations (Agent Initiates)

The agent proactively suggests food based on detected context signals.

#### Time-Based Recommendations

```
Trigger: Current time matches user's typical meal ordering window.
Logic:
  1. Check temporal_pattern.hour_distribution for current hour ± 30 min
  2. If density > threshold AND user hasn't ordered in this window today:
     → Generate time-based nudge
  3. Select top 3 candidates by score_candidate() filtered to current meal type
  4. Apply nudge engine for framing

Example flow:
  Context: Tuesday, 8:45 PM, user's dinner peak is 9 PM
  Signal:  73% of dinners are 8:30-9:30 PM, user hasn't ordered dinner
  Action:  "Your usual dinner time! How about [top 3 from Food DNA]?"

MCP calls required:
  - get_food_orders (check if ordered today)
  - search_restaurants (top candidates) or your_go_to_items (if habitual)
```

#### Pattern-Based Recommendations

```
Trigger: Day-of-week or recurring temporal pattern detected.
Logic:
  1. Check habit_profile.temporal_habits for current day + time
  2. If matching habit found with strength > 0.5:
     → Generate pattern-based nudge
  3. Reference the habit explicitly (psychological reinforcement)

Example flow:
  Context: Friday, 7 PM
  Habit:   "friday_biryani" — strength 0.8, cue="Friday evening", routine="biryani", reward="weekend celebration"
  Action:  "Friday vibes! Your usual biryani from Meghana Foods?"

MCP calls required:
  - get_food_orders (confirm habit pattern)
  - search_restaurants("biryani", addressId) — verify availability
```

#### Context-Based Recommendations

```
Trigger: External context signal (weather, location, time anomaly).
Logic:
  1. Monitor external signals: weather API, calendar, location change
  2. Map context to food psychology:
     - Rain → comfort food bias (+40%)
     - Temperature > 35°C → cold/light food bias
     - Location change (travel) → local cuisine suggestions
     - Late night (unusual) → comfort food, quick delivery
  3. Apply context modifier to scoring function

Example flow:
  Context: Heavy rain detected in user's city at 6 PM
  Food DNA: comfort_foods = ["pakora", "chai", "soup"]
  Action:  "It's raining! Perfect for hot pakoras from Chaat Street. 🌧️"

MCP calls required:
  - Weather API (external, not MCP)
  - search_restaurants("pakora", addressId) — find open restaurants
```

#### Festival-Based Recommendations

```
Trigger: Festival calendar match (Indian festivals with food associations).
Logic:
  1. Check festival calendar for today ± 2 days
  2. Match festival foods to user's dietary identity and regional identity
  3. Adjust price sensitivity DOWN (festival spending tolerance increases)
  4. Generate festival-aware nudge

Example flow:
  Context: Diwali tomorrow
  Food DNA: regional="north_indian", dietary="vegetarian"
  Festival foods: ["mithai", "namkeen", "dry_fruits"]
  Action:  "Diwali tomorrow! 🪔 Order traditional mithai for the family?"

MCP calls required:
  - search_restaurants("mithai", addressId)
  - search_products("diwali sweets", addressId) — Instamart option
```

### C.3 Reactive Recommendations (User Initiates)

#### "Order Something" → General Recommendation

```
Intent: User wants food but has no specific idea.
Logic:
  1. Check time context → determine meal type
  2. Check emotional state → adjust tone
  3. Check habit strength:
     - High habit (>0.6) → "Your usual [item] from [restaurant]?"
     - Low habit (<0.4) → "Here are 3 options you might enjoy"
  4. Score all available restaurants/items against Food DNA
  5. Return top 3 (voice) or top 5-8 (chat)

MCP calls:
  - get_addresses (current delivery location)
  - get_food_orders (check today's orders, recent patterns)
  - search_restaurants(top_cuisine, addressId) — top cuisine from DNA
  - get_restaurant_menu — if user wants to browse
```

#### "I'm Bored" → Variety-Seeking Recommendation

```
Intent: User wants something different from their usual.
Logic:
  1. Identify user's "comfort zone" from habit_profile
  2. Generate candidates OUTSIDE comfort zone but within identity constraints:
     - Different cuisine (but same dietary compliance)
     - Different restaurant (but similar price range)
     - New item from familiar restaurant
  3. Apply "novelty score" = 1 - similarity_to_habits
  4. Rank by: (0.6 × Food DNA score) + (0.4 × novelty_score)
  5. Frame as exploration, not random: "How about [new thing]? You usually love [related thing]"

Psychological basis: Sensory-specific satiety, variety-seeking behavior

MCP calls:
  - get_food_orders (identify usual items to exclude)
  - search_restaurants("something new", addressId)
  - get_restaurant_menu (browsable options)
```

#### "Something Healthy" → Health-Filtered Recommendation

```
Intent: User wants health-oriented food.
Logic:
  1. Check health_orientation.change_stage:
     - Pre-contemplation → This shouldn't happen (user initiated, so they're at least contemplation)
     - Contemplation → Gentle health framing: "light and fresh" not "diet food"
     - Preparation/Action → Specific health goals, calorie counts
     - Maintenance → Reinforce healthy identity
  2. Filter candidates by IFCT 2017 nutrition score > threshold
  3. Apply identity-consistent framing:
     - "Packed with protein" not "low carb"
     - "Fresh and light" not "diet food"
  4. Still respect taste preferences — healthy doesn't mean bland

MCP calls:
  - search_restaurants("healthy", addressId)
  - get_restaurant_menu — filter by health criteria
  - IFCT 2017 lookup — nutrition scoring
```

#### "Surprise Me" → Controlled Variety

```
Intent: User wants to be surprised but within their comfort zone.
Logic:
  1. Define "surprise zone": items with score_candidate() between 0.4-0.7
     (not top picks, not random — familiar-but-different)
  2. Apply diversity constraint: max 1 item from top 3 cuisines
  3. Include one "wild card" — high novelty score but identity-compliant
  4. Frame with confidence: "Trust me on this one — [item] from [restaurant]. You'll love it."

Psychological basis: Controlled novelty within identity boundaries. User wants surprise, not risk.

MCP calls:
  - search_restaurants (diverse cuisines)
  - get_restaurant_menu (unusual items)
```

### C.4 Cross-Server Recommendations (MCP Fusion)

Cross-server intelligence is the Food DNA Agent's unique capability — combining signals from Food, Instamart, and Dineout that no single server provides.

#### Food + Instamart: "Cook vs Order" Intelligence

```
Scenario: User's favorite restaurant is closed, but they have ingredients at home.
Logic:
  1. Detect: search_restaurants returns availabilityStatus=CLOSED for user's top restaurant
  2. Cross-reference: your_go_to_items (Instamart) for matching ingredients
  3. If cooking_capability != "none":
     → "Your usual from [restaurant] is closed, but you have [ingredients] at home. Want to cook?"
  4. If cooking_capability == "none":
     → "Your usual from [restaurant] is closed. Here are similar alternatives from [other restaurant]"

MCP calls:
  - search_restaurants — detect closure
  - your_go_to_items — check home inventory
  - get_addresses — confirm home address
```

#### Food + Dineout: "Loved Restaurant → Dineout Deal"

```
Scenario: User orders frequently from a restaurant that has a Dineout deal.
Logic:
  1. From get_food_orders: identify top restaurants by order frequency
  2. From search_restaurants_dineout: check if top restaurants have Dineout presence
  3. From get_restaurant_details: check for active deals/offers
  4. If deal found: "You love [restaurant]! They have a [deal] on Dineout — [X]% off dinner for [party_size]?"

MCP calls:
  - get_food_orders (top restaurants)
  - search_restaurants_dineout (cross-reference)
  - get_restaurant_details (deal info)
  - get_available_slots (if user wants to book)
```

#### Instamart + Dineout: "Stock Up Before Dinner Out"

```
Scenario: User has a Dineout booking tonight — suggest Instamart prep items.
Logic:
  1. From get_booking_status: detect upcoming booking today
  2. Check: booking is dinner, party size > 1
  3. From your_go_to_items: check if user stocks pre-dinner items (mouth freshener, snacks, beverages)
  4. If relevant: "Dinner at [restaurant] tonight? Need anything from Instamart before you go? Breath freshener, maybe?"

MCP calls:
  - get_booking_status (upcoming bookings)
  - your_go_to_items (pre-dinner patterns)
  - search_products("mouth freshener", addressId) — if pattern detected
```

---

## D. Nudge Engine Design

### D.1 When to Nudge (Timing Rules)

```python
NUDGE_TIMING_RULES = {
    "pre_meal": {
        "trigger": "user's typical order time - 30 min",
        "condition": "no order in current meal window",
        "max_frequency": "1x per meal window",
        "psychology": "anticipatory habit reinforcement"
    },
    "post_meal_gap": {
        "trigger": "user's typical order interval exceeded by 50%",
        "condition": "no order in expected window",
        "max_frequency": "1x per gap",
        "psychology": "gentle re-engagement, not pressure"
    },
    "context_shift": {
        "trigger": "weather change, festival eve, location change",
        "condition": "context signal is new (not already nudged today)",
        "max_frequency": "1x per context event",
        "psychology": "environmental cue activation"
    },
    "habit_window": {
        "trigger": "habit cue detected (Friday evening, rainy day)",
        "condition": "habit strength > 0.5 AND not already ordered",
        "max_frequency": "1x per habit window",
        "psychology": "habit loop reinforcement"
    }
}
```

### D.2 What to Nudge (Content Selection)

```python
def select_nudge_content(food_dna: FoodDNA, context: Context) -> list:
    """Select top candidates for nudge content."""

    candidates = []

    # 1. Habit-based (highest priority for habitual users)
    if food_dna.habit_profile.overall_habit_strength > 0.5:
        for habit in food_dna.habit_profile.temporal_habits:
            if matches_context(habit, context):
                candidates.append({
                    "type": "habit_reinforcement",
                    "item": habit["routine"],
                    "restaurant": habit.get("restaurant"),
                    "score": habit["strength"] * 1.2  # Habit bonus
                })

    # 2. Emotional-fit (high priority when emotional state detected)
    if context.emotional_state != "neutral":
        emotional_items = get_emotional_items(food_dna, context.emotional_state)
        candidates.extend(emotional_items)

    # 3. Context-fit (weather, festival, time)
    context_items = get_context_items(food_dna, context)
    candidates.extend(context_items)

    # 4. Collaborative (users like you also ordered)
    collab_items = get_collaborative_items(food_dna)
    candidates.extend(collab_items)

    # Deduplicate and rank
    return rank_and_deduplicate(candidates)[:5]
```

### D.3 How to Nudge (Framing Per Psychological Framework)

| Scenario | Framing Strategy | Example |
|----------|-----------------|---------|
| Habit reinforcement | Confirm identity: "Your usual" | "Your usual Friday biryani from Meghana?" |
| Variety seeking | Connect to known: "Like [X] but different" | "Love dosa? Try appam — same South Indian comfort, different texture" |
| Emotional comfort | Serve need first, no judgment | "Tough day? Your comfort curd rice from Saravana Bhavan" |
| Health nudge | Positive framing, never shaming | "Light and fresh option — paneer tikka salad, 320 cal" |
| Festival | Celebrate identity | "Diwali vibes! 🪔 Traditional mithai from [trusted shop]" |
| Price-sensitive | Anchor + savings frame | "₹180 biryani, 40% off — you save ₹120!" |
| Social context | Optimize for group | "Family dinner? Combo for 4 at ₹599 — something for everyone" |
| Decision fatigue | Minimize choices | "Yes or no: your usual masala dosa from Saravana Bhavan?" |

### D.4 When NOT to Nudge (Respect Autonomy)

```python
SUPPRESSION_RULES = {
    "quiet_hours": {
        "condition": "local_time between 23:00 and 08:00",
        "action": "suppress_all",
        "exception": "user has active late_night pattern (>0.2 late_night_ratio)"
    },
    "stress_detected": {
        "condition": "emotional_patterns.stress_level > 0.7",
        "action": "suppress_health_nudges_only",
        "note": "still offer comfort food if appropriate"
    },
    "nudge_fatigue": {
        "condition": "nudge_count_today >= 3",
        "action": "suppress_all",
        "reset": "next_day"
    },
    "user_rejected": {
        "condition": "user dismissed last nudge",
        "action": "suppress_same_type for 4 hours",
        "note": "different nudge types still allowed"
    },
    "explicit_stop": {
        "condition": "user says 'stop suggestions' or similar",
        "action": "suppress_all for 7 days",
        "reset": "user re-engages"
    },
    "dietary_fast": {
        "condition": "fasting period detected (Navratri, Ramadan, Ekadashi)",
        "action": "suppress_non_compliant_nudges",
        "note": "offer fasting-appropriate food only"
    }
}
```

### D.5 Nudge Intensity Levels

| Level | Behavior | When to Use | Example |
|-------|----------|-------------|---------|
| **Suggestion** | Subtle, dismissible, one option | Low confidence, gentle context | "By the way, it's raining ☔" |
| **Recommendation** | 2-3 options with reasoning | Medium confidence, clear pattern | "It's Friday! Your usual biryani, or want to try Hyderabadi?" |
| **Reminder** | Direct, action-oriented | High confidence, strong habit | "Your usual dinner is ready to order. One tap to confirm." |

Intensity selection:
```python
def select_intensity(food_dna, context, nudge_type):
    if food_dna.confidence_score < 0.3:
        return "suggestion"
    if nudge_type == "habit_reinforcement" and food_dna.habit_profile.overall_habit_strength > 0.7:
        return "reminder"
    if context.emotional_state in ["stressed", "tired"]:
        return "suggestion"  # Don't add cognitive load
    return "recommendation"  # Default
```

---

## E. Prediction Models

### E.1 Next Order Time Prediction

**Approach**: Time series forecasting on order timestamps.

```python
# Data: Array of order timestamps → inter-order intervals (hours)
# Model: Prophet / Darts (ARIMA) with:
#   - Daily seasonality (meal times)
#   - Weekly seasonality (weekday vs weekend)
#   - Holiday regressors (festival calendar)

def predict_next_order(order_timestamps: list) -> dict:
    """Predict when user will next order."""
    intervals = compute_intervals(order_timestamps)
    model = Prophet(daily_seasonality=True, weekly_seasonality=True)
    model.fit(intervals)
    forecast = model.predict(next_n=1)
    return {
        "predicted_time": forecast["yhat"],
        "confidence_interval": (forecast["yhat_lower"], forecast["yhat_upper"]),
        "likely_meal": classify_meal(forecast["yhat"])  # breakfast/lunch/dinner/snack
    }
```

**MCP data source**: `get_food_orders` → timestamps
**Library**: Darts (unit8co/darts) — Prophet, ARIMA, Neural Networks
**Target accuracy**: ±30 minutes for users with 20+ orders

### E.2 Cuisine Prediction

**Approach**: Multi-class classification weighted by Food DNA.

```python
def predict_cuisine(food_dna: FoodDNA, context: Context) -> list:
    """Predict most likely cuisine for current context."""

    # Base: cuisine_affinity from Food DNA
    scores = dict(food_dna.regional_identity.cuisine_affinity)

    # Time modifier: breakfast → South Indian bias, dinner → diverse
    time_mod = get_time_cuisine_modifier(context.current_hour)
    scores = apply_modifier(scores, time_mod)

    # Day modifier: weekend → indulgent, weekday → practical
    day_mod = get_day_cuisine_modifier(context.day_of_week)
    scores = apply_modifier(scores, day_mod)

    # Emotional modifier: stress → comfort cuisine, celebration → premium
    emotion_mod = get_emotional_cuisine_modifier(food_dna.emotional_patterns)
    scores = apply_modifier(scores, emotion_mod)

    # Sort and return top 3
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
```

**MCP data source**: `get_food_orders` → cuisine tags per order
**Target accuracy**: >70% top-3 hit rate

### E.3 Restaurant Prediction

**Approach**: Collaborative filtering (SVD) + content-based (restaurant attributes).

```python
def predict_restaurant(food_dna: FoodDNA, cuisine: str, context: Context) -> list:
    """Predict best restaurants for current context."""

    candidates = []

    # 1. Habitual restaurants (loyalty bonus)
    for rest in food_dna.habit_profile.recurring_restaurants:
        if rest["cuisine"] == cuisine:
            candidates.append({
                "restaurant": rest["name"],
                "score": rest["strength"] * 0.4,  # Loyalty weight
                "source": "habit"
            })

    # 2. Content-based (restaurant attributes match Food DNA)
    for rest in get_restaurants_by_cuisine(cuisine, context.address_id):
        attr_score = compute_attribute_match(rest, food_dna)
        candidates.append({
            "restaurant": rest["name"],
            "score": attr_score * 0.35,
            "source": "content"
        })

    # 3. Collaborative (users with similar Food DNA also ordered)
    similar_users = find_similar_profiles(food_dna)
    for rest in get_popular_among_similar(similar_users, cuisine):
        candidates.append({
            "restaurant": rest["name"],
            "score": rest["similarity"] * 0.25,
            "source": "collaborative"
        })

    return deduplicate_and_rank(candidates)[:5]
```

**MCP data source**: `get_food_orders` → restaurant names, `search_restaurants` → attributes
**Algorithm**: Hybrid SVD + TF-IDF (reference: zyna-b/Food-Recommendation-System)
**Target accuracy**: >60% top-3 hit rate

### E.4 Meal Planning (Sequence Pattern Mining)

**Approach**: Detect sequential ordering patterns (A→B→C).

```python
def detect_meal_sequences(order_history: list) -> list:
    """Find recurring sequences in ordering behavior."""

    # Group orders by day
    daily_orders = group_by_day(order_history)

    # Extract sequences: what follows what?
    sequences = []
    for i in range(len(daily_orders) - 1):
        today = daily_orders[i]
        tomorrow = daily_orders[i + 1]
        sequences.append((today.cuisine, tomorrow.cuisine))

    # Find frequent sequences (support > 0.1)
    frequent = apriori(sequences, min_support=0.1)

    # Example outputs:
    # "South Indian breakfast → North Indian dinner" (support: 0.35)
    # "Heavy Friday dinner → Light Saturday breakfast" (support: 0.28)
    # "Chinese lunch → Indian dinner" (support: 0.22)

    return frequent
```

**MCP data source**: `get_food_orders` → full order history
**Algorithm**: Sequential pattern mining (PrefixSpan or similar)
**Use case**: "Yesterday you had biryani for dinner — lighter breakfast today?"

---

## F. MCP Integration Specifications

### F.1 Tool Calls Per Recommendation Type

| Recommendation Type | MCP Tools Called | Call Order | Rate Impact |
|--------------------|-----------------|------------|-------------|
| Time-based proactive | `get_food_orders`, `search_restaurants` | 2 calls | Low |
| Pattern-based proactive | `get_food_orders`, `search_restaurants` | 2 calls | Low |
| Context-based (weather) | `search_restaurants` | 1 call | Minimal |
| Festival-based | `search_restaurants` OR `search_products` | 1 call | Minimal |
| "Order something" | `get_addresses`, `get_food_orders`, `search_restaurants` | 3 calls | Medium |
| "I'm bored" | `get_food_orders`, `search_restaurants` (2 queries) | 3 calls | Medium |
| "Something healthy" | `search_restaurants`, `get_restaurant_menu` | 2 calls | Low |
| "Surprise me" | `search_restaurants` (3 queries) | 3 calls | Medium |
| Food + Instamart fusion | `search_restaurants`, `your_go_to_items` | 2 calls | Low |
| Food + Dineout fusion | `get_food_orders`, `search_restaurants_dineout`, `get_restaurant_details` | 3 calls | Medium |
| Instamart + Dineout fusion | `get_booking_status`, `your_go_to_items` | 2 calls | Low |

### F.2 Response Parsing Logic

```python
def parse_search_restaurants(response: dict, channel: str) -> list:
    """Parse restaurant search results for recommendation display."""
    restaurants = response.get("restaurants", [])
    parsed = []
    for r in restaurants:
        if r["availabilityStatus"] != "OPEN":
            continue  # Skip closed restaurants for recommendations
        parsed.append({
            "id": r["restaurantId"],
            "name": r["name"],
            "rating": r.get("rating"),
            "delivery_time": r["deliveryTimeSpoken"] if channel == "voice" else r["deliveryTimeRange"],
            "description": r["shortDescription"] if channel == "voice" else r["longDescription"],
            "distance": r.get("distance"),
        })
    return parsed

def parse_go_to_items(response: dict) -> list:
    """Parse go-to items for quick reorder suggestions."""
    items = response.get("items", [])
    return [{
        "name": item["name"],
        "spinId": item["spinId"],
        "price": item.get("price"),
        "frequency": item.get("orderFrequency"),
        "last_ordered": item.get("lastOrderDate"),
    } for item in items]

def parse_booking_status(response: dict) -> list:
    """Parse booking status for cross-server intelligence."""
    bookings = response.get("bookings", [])
    return [{
        "bookingId": b["bookingId"],
        "restaurant": b.get("restaurantName"),
        "date": b.get("bookingDate"),
        "time": b.get("bookingTime"),
        "partySize": b.get("partySize"),
        "status": b["status"],
    } for b in bookings if b["status"] in ["CONFIRMED", "PENDING"]]
```

### F.3 Error Handling Per Tool

| Tool | Common Error | Handling Strategy |
|------|-------------|-------------------|
| `search_restaurants` | No results for query | Broaden query (remove specificity), suggest alternatives |
| `get_restaurant_menu` | Restaurant closed | Mark as unavailable, suggest similar open restaurants |
| `update_food_cart` | Cart flush (switched restaurant) | Warn user before switching, confirm intent |
| `get_food_cart` | Cart expired/empty | Re-suggest items, offer quick reorder |
| `place_food_order` | 5xx error | Do NOT retry. Call `get_food_orders` first to check |
| `place_food_order` | Cart cap ₹1,000 exceeded | Suggest splitting order or removing items |
| `your_go_to_items` | Empty (new user) | Fall back to popular items + dietary filter |
| `search_products` | No results | Suggest related products, broaden search |
| `checkout` (Instamart) | Below ₹99 minimum | Suggest complementary items to reach minimum |
| `book_table` | No slots available | Suggest alternate times or restaurants |
| `track_food_order` | Poll rate too fast | Enforce ≥10s interval, queue updates |

### F.4 Rate Limit Compliance

**Target**: Stay under 120 requests/min per user.

```python
class RateLimiter:
    """MCP rate limiter for recommendation engine."""

    def __init__(self, max_per_minute=100):  # 100 to leave 20% headroom
        self.max_per_minute = max_per_minute
        self.requests = []

    def can_call(self) -> bool:
        now = time.time()
        self.requests = [r for r in self.requests if now - r < 60]
        return len(self.requests) < self.max_per_minute

    def record_call(self):
        self.requests.append(time.time())

    def batch_recommendation_calls(self, tools: list) -> list:
        """Batch multiple tool calls where possible to reduce total requests."""
        # Deduplicate: if search_restaurants called twice with same params, merge
        unique_calls = deduplicate_calls(tools)
        # Sequence: run independent calls in parallel (if SDK supports)
        return unique_calls
```

**Optimization strategies**:
- Cache `get_food_orders` results for 5 minutes per session
- Cache `search_restaurants` results for 10 minutes per address+query
- Batch feature extraction (don't call MCP tools redundantly)
- Pre-compute Food DNA during off-peak (background job, not request path)

---

## G. Voice vs Chat Response Shaping

### G.1 Voice Response Rules

| Rule | Implementation |
|------|---------------|
| Max 3 options | Truncate results to top 3 by score |
| Spoken prices | Use `deliveryTimeSpoken`, format prices as "one eighty rupees" |
| Short descriptions | Use `shortDescription` from MCP responses |
| 1-2 sentences per option | "Meghana Foods biryani, one eighty rupees, thirty minutes" |
| Natural confirmations | "Want me to order that?" not "Please confirm your selection" |
| Error recovery | "That place is closed. How about [alternative]?" |

```python
def shape_voice_response(recommendations: list) -> str:
    """Format recommendations for voice output."""
    top_3 = recommendations[:3]
    if len(top_3) == 1:
        r = top_3[0]
        return f"How about {r['name']}? {r['short_description']}. {r['delivery_time_spoken']}. Want me to order?"
    else:
        options = ". ".join([
            f"{i+1}. {r['name']} — {r['short_description']}, {r['price_spoken']}"
            for i, r in enumerate(top_3)
        ])
        return f"Here are your top picks: {options}. Which one?"
```

### G.2 Chat Response Rules

| Rule | Implementation |
|------|---------------|
| Up to 8 options | Full ranked list, scrollable |
| Rich details | Use `longDescription`, full price breakdown, ratings |
| Markdown formatting | Bold names, bullet lists, emoji for visual appeal |
| Widgets | Restaurant cards, menu items, "Order Now" buttons |
| Delivery time range | Use `deliveryTimeRange` ("30-40 min") |
| Action buttons | "Reorder", "View Menu", "Add to Cart" |

```python
def shape_chat_response(recommendations: list) -> str:
    """Format recommendations for chat output with markdown."""
    lines = ["🍽️ **Your personalized picks:**\n"]
    for i, r in enumerate(recommendations[:8]):
        lines.append(
            f"**{i+1}. {r['name']}** ⭐ {r['rating']}\n"
            f"   {r['long_description']}\n"
            f"   💰 ₹{r['price']} · 🕐 {r['delivery_time_range']}\n"
        )
    lines.append("\nTap a restaurant to view menu, or say the number to order!")
    return "\n".join(lines)
```

### G.3 Channel Detection

```python
def detect_channel(context: dict) -> str:
    """Detect whether interaction is voice or chat."""
    if context.get("surface") == "voice":
        return "voice"
    if context.get("input_type") == "speech":
        return "voice"
    return "chat"  # Default to chat
```

---

## H. Implementation Roadmap

### H.1 MVP Features (Must-Have for Demo)

| # | Feature | Priority | MCP Tools | Effort |
|---|---------|----------|-----------|--------|
| 1 | Food DNA profile from `get_food_orders` | P0 | `get_food_orders` | 2 days |
| 2 | Dietary identity detection | P0 | `get_food_orders`, `your_go_to_items` | 1 day |
| 3 | "Order something" reactive recommendation | P0 | `get_addresses`, `search_restaurants` | 1 day |
| 4 | Friday biryani pattern detection | P0 | `get_food_orders` | 0.5 day |
| 5 | Voice response shaping (3 options) | P0 | N/A | 0.5 day |
| 6 | Chat response shaping (8 options) | P0 | N/A | 0.5 day |
| 7 | Basic nudge engine (time + habit) | P1 | N/A | 1 day |
| 8 | "Something healthy" health filter | P1 | `search_restaurants`, IFCT 2017 | 1 day |
| 9 | Rain/weather context detection | P1 | Weather API + `search_restaurants` | 0.5 day |
| 10 | Festival awareness (Diwali, Holi) | P1 | Festival calendar | 0.5 day |

**MVP total**: ~9 days of implementation
**Demo scenarios covered**:
- "Order my usual" → Food DNA lookup → reorder
- "It's Friday, your usual biryani?" → pattern detection
- "It's raining" → context-based comfort food
- Voice: 3 options with spoken prices
- Chat: 8 options with rich details

### H.2 V2 Features (Post-Demo Enhancement)

| # | Feature | Priority | Dependencies |
|---|---------|----------|-------------|
| 1 | Cross-server fusion (Food + Instamart) | V2 | Instamart MCP integration |
| 2 | Cross-server fusion (Food + Dineout) | V2 | Dineout MCP integration |
| 3 | Emotional state detection | V2 | 30+ order history |
| 4 | Life-stage transition detection | V2 | 60+ order history |
| 5 | Collaborative filtering (SVD) | V2 | User similarity data |
| 6 | Sequence pattern mining (meal planning) | V2 | 90+ order history |
| 7 | Full nudge engine (all intensity levels) | V2 | All prediction models |
| 8 | Anomaly detection (dietary shift alerts) | V2 | Robust baseline |
| 9 | NRI cross-timezone ordering | V2 | Multi-address intelligence |
| 10 | Multi-user household modeling | V2 | Family order pattern detection |

### H.3 Performance Targets

| Metric | MVP Target | V2 Target | Measurement |
|--------|-----------|-----------|-------------|
| Dietary compliance | 100% | 100% | Zero non-compliant recommendations |
| Recommendation acceptance | >50% | >65% | Accepted / Total suggestions |
| Response latency (voice) | <2s | <1.5s | Time to first recommendation |
| Response latency (chat) | <3s | <2s | Time to full recommendation list |
| MCP calls per recommendation | ≤4 | ≤3 | Rate limit compliance |
| Cold start satisfaction | >40% | >55% | User acceptance within first 5 orders |
| Habit detection accuracy | >70% | >85% | Correctly identified recurring patterns |
| Time prediction accuracy | ±60 min | ±30 min | Next order time deviation |
| Voice naturalness | Acceptable | Excellent | Human evaluation score |
| Error recovery rate | >80% | >95% | Successful fallback when primary fails |

---

## Appendix: Quick Reference

### Scoring Weights

```
Dietary Identity:    HARD FILTER (0 or 1)
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

### Learning Rates

```
Dietary Identity:    0.00 (never updates automatically)
Regional Identity:   0.02
Cuisine Preferences: 0.10
Temporal Patterns:   0.20
Price Psychology:    0.15
Health Orientation:  0.05
Social Dynamics:     0.20
Emotional Patterns:  0.50
Life Stage:          0.05
Habit Profile:       0.05
```

### MCP Rate Budget (per user per minute)

```
Total budget:     120 req/min
Recommendation:   ~100 req/min (headroom for tracking, cart, orders)
Per recommendation: ≤4 calls (MVP), ≤3 calls (V2)
Max recommendations: 25/min (theoretical), ~5/min (practical)
```

### Key MCP Tools Quick Reference

| Tool | Server | Key Fields |
|------|--------|------------|
| `get_food_orders` | Food | orders[], timestamp, items, total |
| `search_restaurants` | Food | restaurantId, availabilityStatus, deliveryTimeSpoken/Range |
| `get_restaurant_menu` | Food | categories[], items[], variants[], addOns[] |
| `your_go_to_items` | Instamart | items[], spinId, orderFrequency |
| `search_products` | Instamart | productId, variants[].spinId, price |
| `get_booking_status` | Dineout | bookingId, status, restaurantName, partySize |
| `search_restaurants_dineout` | Dineout | restaurantId, offers, cuisines, rating |

---

*Phase 2 deliverable complete. This specification provides the algorithmic foundation for Phase 3 (MCP Integration & Agent Build).*
