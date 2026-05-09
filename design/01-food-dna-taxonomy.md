# Food DNA Taxonomy — Phase 1 Design Document

> **Project**: Food DNA Agent (Swiggy Builders Club)
> **Phase**: 1 — Taxonomy & Scoring System
> **Date**: 2026-05-09
> **Status**: Design Complete

---

## A. Taxonomy Overview

### What Is Food DNA?

Food DNA is a multi-dimensional behavioral profile that captures **why** a user eats what they eat, **when** they eat it, and **how** it connects to who they are. It is not a preference list — it is a psychological fingerprint built from behavioral signals across Swiggy's three MCP servers (Food, Instamart, Dineout).

### Why It Matters

Traditional recommendation systems model food as data: collaborative filtering ("users like you ordered X"), content-based filtering ("this dish matches your taste profile"). Food DNA models food as **psychology**: identity, habit, emotion, culture, social dynamics, and life context.

**The difference in practice:**

| Traditional Profile | Food DNA |
|---|---|
| "Likes biryani" | "Has a Friday celebration habit loop — biryani is the routine that satisfies weekend reward-seeking. If unavailable, wants something equally indulgent, not a salad." |
| "Vegetarian" | "Vegetarian by dharma (Hindu, South Indian family). Eggetarian outside the home. Never suggest non-veg — it's identity, not preference." |
| "Orders at 8 PM" | "Orders dinner at 9 PM on weekdays (post-commute wind-down), 7 PM on weekends (family dinner with kids). Late-night orders signal stress." |
| "Budget: ₹200-300" | "Moderate spender, high coupon sensitivity. Frames value as savings, not cheapness. Show original price + discount always." |

### How It Differs from Traditional Profiles

1. **Psychology-first**: Models cognitive biases, emotional states, habit loops — not just item co-occurrence
2. **Identity-level constraints**: Dietary identity (Jain, halal) is non-negotiable, not an optimization target
3. **Cross-server fusion**: Combines grocery (Instamart) + restaurant (Food) + dining out (Dineout) into one profile
4. **Temporal awareness**: Same user wants different food at 8 AM vs 8 PM
5. **Life-stage aware**: A college student and a senior citizen both "like dosa" but for completely different reasons
6. **Emotionally intelligent**: Detects stress, celebration, boredom from ordering patterns and responds accordingly
7. **Culturally grounded**: Built for Indian food psychology — regional pride, festival food, joint family dynamics

---

## B. The 10 Dimensions of Food DNA

### Dimension 1: Dietary Identity

**Definition**: The user's fundamental dietary classification rooted in religious, moral, and cultural identity. This is the **highest-priority, non-negotiable dimension** — it is never overridden by the model.

**Psychological Basis**: Self-affirmation theory (Steele, 1988). Dietary choices in India are identity expressions, not preferences. A Jain user avoiding onion/garlic is affirming their religious identity, not making a taste choice. Pew Research (2021) shows 81% of Indians limit meat consumption in some way.

**Scoring System**:
```
Primary: Categorical (non-overridable)
  - "vegetarian"     — No meat, no egg, no fish
  - "eggetarian"     — No meat/fish, but eats egg
  - "non_vegetarian" — Eats meat, fish, egg
  - "jain"           — Vegetarian + no root vegetables, no onion/garlic, no after sunset
  - "vegan"          — No animal products at all

Sub-fields (continuous 0-1):
  strictness: 0.0-1.0     — How strictly they follow (0 = flexible, 1 = absolute)
  home_vs_outside: 0.0-1.0 — 0 = same everywhere, 1 = different rules at home vs outside
  fasting_frequency: 0.0-1.0 — How often they observe fasts (Navratri, Ekadashi, Ramadan)
```

**MCP Signal Mapping**:
- `your_go_to_items` → Grocery items reveal dietary identity (no meat products for vegetarians)
- `get_food_orders` → Restaurant orders confirm dietary pattern
- `search_restaurants` → Search filters reveal dietary preference
- `get_restaurant_menu` → Items browsed confirm identity

**Update Rate**: **Near-zero**. Set once (explicitly or inferred from first 5 orders), rarely changes. A shift from vegetarian to non-vegetarian is a major life event, not a preference drift.

**Indian-Specific Considerations**:
- "Pure vegetarian" restaurants vs "veg options available" — vegetarians need the former
- "Eggetarian" is a uniquely Indian category (Western taxonomy lacks this)
- "Veg at home, non-veg outside" is a common pattern — model must handle duality
- Jain restrictions (no root vegetables, no eating after sunset) require restaurant-level filtering
- Halal requirements for Muslim users need supply-side verification
- Fasting patterns are religiously prescribed, not health-motivated

---

### Dimension 2: Regional Cultural Identity

**Definition**: The user's food identity rooted in geographic and cultural origin — which regional cuisine tradition shapes their palate, comfort food, and food rituals.

**Psychological Basis**: Cultural psychology and identity theory. Regional food identity is deeply ingrained through childhood socialization. A Bengali's fish-centric palate, a Gujarati's sweet-sour balance, a Keralite's coconut oil preference — these are identity markers, not mere preferences. Research from ScienceDirect (2020) confirms food as a primary expression of cultural identity in multicultural societies.

**Scoring System**:
```
Primary: Categorical
  region: "south_indian" | "north_indian" | "west_indian" | "east_indian" | "northeast_indian"
  state: "karnataka" | "tamil_nadu" | "andhra" | "telangana" | "kerala" | "maharashtra" | "gujarat" | "rajasthan" | "punjab" | "delhi" | "uttar_pradesh" | "bengal" | "odisha" | "assam" | ... (28 states)

Sub-fields (continuous 0-1):
  cuisine_affinity: {"south_indian": 0.65, "north_indian": 0.15, "chinese": 0.10, "italian": 0.05, "other": 0.05}
  rice_vs_wheat: 0.0-1.0  — 0 = wheat-dominant (North), 1 = rice-dominant (South/East)
  spice_tolerance: 0.0-1.0 — 0 = mild, 1 = very spicy
  sweetness_preference: 0.0-1.0 — Gujarati/Bengali higher, others lower
```

**MCP Signal Mapping**:
- `get_food_orders` → Cuisine distribution, restaurant types, dish names
- `search_restaurants` → Cuisine search queries
- `your_go_to_items` → Grocery items reveal regional staples (rice vs wheat, regional brands)
- `get_addresses` → Current location vs origin (may differ for migrants)

**Update Rate**: **Very slow** (learning rate: 0.02). Regional identity is established early and changes rarely. However, migrants may develop dual affinity over years.

**Indian-Specific Considerations**:
- South Indian breakfast (dosa, idli) vs North Indian breakfast (paratha, poha) — different meal structures
- "Best biryani is from Hyderabad" — regional pride drives restaurant choice
- Rice vs wheat is a fundamental divide (South+East = rice, North+West = wheat)
- Regional festivals have specific foods (Pongal in Tamil Nadu, Onam in Kerala, Durga Puja in Bengal)
- Spice tolerance varies dramatically by region (Andhra = very high, Gujarati = lower)

---

### Dimension 3: Cuisine Preferences

**Definition**: Granular preferences for specific cuisine types, flavor profiles, and food categories beyond the regional identity.

**Psychological Basis**: Sensory-specific satiety and variety-seeking behavior. While regional identity sets the baseline, users develop preferences for non-native cuisines through exposure, social influence, and novelty-seeking. The balance between comfort (familiar) and exploration (novel) is a key personality trait.

**Scoring System**:
```
Cuisine distribution (continuous, sums to 1.0):
  south_indian: 0.0-1.0
  north_indian: 0.0-1.0
  chinese: 0.0-1.0
  italian: 0.0-1.0
  continental: 0.0-1.0
  street_food: 0.0-1.0
  dessert: 0.0-1.0
  fast_food: 0.0-1.0
  healthy: 0.0-1.0
  other: 0.0-1.0

Flavor profile (continuous 0-1):
  spice_level: 0.0-1.0     — Preference for spicy food
  sweet_level: 0.0-1.0     — Preference for sweet flavors
  tangy_level: 0.0-1.0     — Preference for tangy/sour
  umami_level: 0.0-1.0     — Preference for savory/umami
```

**MCP Signal Mapping**:
- `get_food_orders` → Cuisine tags, dish names, restaurant types
- `search_restaurants` → Cuisine search queries
- `get_restaurant_menu` → Items browsed (exploration signals)
- `search_products` (Instamart) → Ingredient preferences

**Update Rate**: **Slow** (learning rate: 0.10). Preferences are stable but shift with exposure, life stage, and social influence.

**Indian-Specific Considerations**:
- "Chinese" in India = Indian-Chinese (Manchurian, hakka noodles) — not authentic Chinese
- Street food is a legitimate cuisine category in India (vada pav, pani puri, chaat)
- "Continental" is an Indian catch-all for Western food
- Dessert preferences are festival-linked (mithai culture)

---

### Dimension 4: Temporal Patterns

**Definition**: When the user orders, how often, and how their food behavior maps to time-of-day, day-of-week, and seasonal rhythms.

**Psychological Basis**: Chronobiology and habit loop theory. Human food preferences change throughout the day based on circadian rhythms, blood sugar, energy needs, and psychological state. The same user who wants idli-dosa at 8 AM wants biryani at 9 PM. The research shows lunch ordering peak shifted from 12:30 to 1:30 PM (flexible work) and late-night ordering grew 200%+ in metros.

**Scoring System**:
```
Hour distribution (24-element vector, sums to 1.0):
  hour_0 through hour_23 — proportion of orders in each hour

Day-of-week distribution (7-element vector, sums to 1.0):
  monday through sunday — proportion of orders on each day

Derived metrics (continuous 0-1):
  breakfast_regularity: 0.0-1.0  — Consistency of morning ordering
  lunch_regularity: 0.0-1.0      — Consistency of lunch ordering
  dinner_regularity: 0.0-1.0     — Consistency of dinner ordering
  late_night_ratio: 0.0-1.0      — Proportion of orders after 10 PM
  weekend_ratio: 0.0-1.0         — Weekend vs weekday ordering
  order_interval_days: float     — Average days between orders
  order_regularity: 0.0-1.0      — Consistency of ordering frequency
```

**MCP Signal Mapping**:
- `get_food_orders` → Timestamps of all orders
- `get_food_order_details` → Specific order timing
- `your_go_to_items` → Order dates for recurring items
- `get_booking_status` → Dining out timing

**Update Rate**: **Medium** (learning rate: 0.20, rolling 30-day window). Timing patterns shift with work schedule, season, and life stage.

**Indian-Specific Considerations**:
- South Indian breakfast culture (tiffin) is strong — 7-9 AM ordering is habitual
- "Chai time" (4-6 PM) is a distinct ordering occasion, not a meal
- Dinner timing: 7 PM in South, 9 PM in North — regional variation is significant
- Late-night ordering (10 PM-1 AM) is massive in Delhi NCR, Mumbai, Bengaluru
- Festival days have specific meal timing (Diwali sweets, Holi snacks)
- Ramadan shifts Muslim users' entire temporal pattern for a month

---

### Dimension 5: Price Psychology

**Definition**: How the user perceives, evaluates, and responds to price — including budget range, coupon sensitivity, value framing, and deal-seeking behavior.

**Psychological Basis**: Behavioral economics — anchoring bias, loss aversion, and framing effects. Indian users are price-sensitive but not cheap: they want VALUE. "₹200 for biryani" feels expensive, but "₹200 for biryani, and you saved ₹80 with your coupon" feels like a win. The agent controls the anchor and the frame.

**Scoring System**:
```
Primary metrics (continuous):
  avg_order_value: float (₹) — Average spend per order
  aov_std: float (₹) — Standard deviation (consistency)
  price_sensitivity: 0.0-1.0 — 0 = price-insensitive, 1 = very sensitive
  coupon_usage_rate: 0.0-1.0 — Proportion of orders with coupons
  deal_seeking: 0.0-1.0 — Active search for deals/coupons
  premium_frequency: 0.0-1.0 — How often they order premium/expensive

Derived:
  budget_tier: "budget" | "value" | "moderate" | "comfortable" | "premium"
  value_framing: "savings" | "quality" | "convenience" — What "value" means to them
```

**MCP Signal Mapping**:
- `get_food_orders` → Order totals, price patterns
- `fetch_food_coupons` → Coupon usage, deal-seeking behavior
- `apply_food_coupon` → Active coupon application
- `search_restaurants` → Price-filtered searches
- `get_restaurant_menu` → Items browsed by price range

**Update Rate**: **Medium** (learning rate: 0.15). Price sensitivity shifts with income changes, life stage, and Swiggy One membership status.

**Indian-Specific Considerations**:
- Always show original price + discount together (anchoring + loss aversion framing)
- "You saved ₹X" is more motivating than "Get ₹X off" (endowment effect)
- Swiggy One savings should be a persistent psychological anchor
- ₹50 discount feels huge to a student, irrelevant to a premium user
- Combo pricing ("meal for 2 at ₹299") is effective value framing
- Festival spending is less price-sensitive (celebration budget)

---

### Dimension 6: Health Orientation

**Definition**: The user's relationship with health, nutrition, and dietary goals — from "I eat whatever" to medically necessary restrictions.

**Psychological Basis**: Health Belief Model and Transtheoretical Model (Stages of Change). Health orientation exists on a spectrum: pre-contemplation ("I eat whatever"), contemplation ("maybe I should eat better"), preparation ("I want to change"), action ("I'm eating healthier"), maintenance ("healthy eating is my norm"). The agent must DETECT the stage and match intervention intensity accordingly. Never push health on someone in pre-contemplation.

**Scoring System**:
```
Primary (continuous 0-1):
  health_awareness: 0.0-1.0 — How health-conscious the user is
  calorie_awareness: 0.0-1.0 — How much they consider calories
  health_trend: -1.0 to 1.0  — Declining to improving trajectory

Categorical:
  change_stage: "pre_contemplation" | "contemplation" | "preparation" | "action" | "maintenance"
  dietary_goal: "none" | "weight_loss" | "muscle_gain" | "diabetic" | "heart_healthy" | "general_wellness"
  medical_restrictions: [] — List of medical dietary needs

Derived (continuous 0-1):
  avg_health_score: 0.0-1.0 — Average nutritional quality of orders (using IFCT 2017)
  healthy_order_ratio: 0.0-1.0 — Proportion of "healthy" orders
  weekday_vs_weekend_health: float — Difference in health behavior
```

**MCP Signal Mapping**:
- `get_food_orders` → Food categories, health-related items
- `search_restaurants` → Health-related search queries ("healthy", "salad", "protein")
- `your_go_to_items` → Grocery items (healthy vs processed)
- `get_restaurant_menu` → Health items browsed

**Update Rate**: **Very slow** (learning rate: 0.05). Health orientation is a stable trait that changes gradually with life events (diagnosis, fitness goal, age).

**Indian-Specific Considerations**:
- "Healthy" in India = "ghar ka khana" (home food), not "low-calorie" — use Indian framing
- "Satvic" food philosophy = pure, clean, promotes clarity — cultural health concept
- Fasting is religious, not health-motivated — don't conflate
- "Diet food" has negative connotations — use "light and fresh" instead
- Medical dietary needs (diabetic, heart) are common in 40+ age group
- Protein awareness is growing but still lower than Western markets

---

### Dimension 7: Social Dynamics

**Definition**: Whether the user eats alone, with family, with friends, or hosts guests — and how social context changes food behavior.

**Psychological Basis**: Social psychology and commensality research. Food in India is deeply social — the decision unit is often the family, not the individual. Research shows "commensality" (eating together) is linked to well-being. Joint family ordering involves 6-15 people with different preferences, where "something for everyone" matters more than individual optimization.

**Scoring System**:
```
Primary distribution (continuous, sums to 1.0):
  solo_ratio: 0.0-1.0       — Proportion of solo orders
  couple_ratio: 0.0-1.0     — Proportion of 2-person orders
  family_ratio: 0.0-1.0     — Proportion of family orders (3+)
  group_ratio: 0.0-1.0      — Proportion of large group orders
  treat_ratio: 0.0-1.0      — Proportion of orders sent to others

Derived:
  avg_party_size: float      — Estimated average people per order
  primary_social_context: "solo" | "couple" | "family" | "group" | "mixed"
  hospitality_frequency: 0.0-1.0 — How often they host/order for guests
  multi_address_ratio: 0.0-1.0 — Orders to non-home addresses
```

**MCP Signal Mapping**:
- `get_food_orders` → Order size (items), total amount, frequency
- `get_addresses` → Home, work, friend's address patterns
- `get_booking_status` → Dining out party size, occasion type
- `get_food_order_details` → Order composition (single vs multiple items)

**Update Rate**: **Medium** (learning rate: 0.20). Social dynamics shift with life stage (single → married → parent), but are stable within a stage.

**Indian-Specific Considerations**:
- Joint family ordering: agent must optimize for the family unit, not the individual
- "Ordering for 2" often means "I'm treating someone" — social occasion
- Indians over-order when hosting (generosity signaling) — suggest 20-30% more
- Children's preferences often drive family orders
- Elderly dietary restrictions constrain family options
- NRI ordering for parents is a distinct social dynamic

---

### Dimension 8: Emotional Patterns

**Definition**: How emotional states — stress, celebration, boredom, loneliness — influence food choices and ordering behavior.

**Psychological Basis**: Emotional eating research (PMC4214609, 2014). People eat differently when stressed, happy, sad, bored, or celebrating. The agent detects emotional states from ordering patterns and responds by serving the emotional need first, not pushing long-term goals. Key insight: **never push healthy food on a stressed user** — their immediate emotional need (comfort) takes priority.

**Scoring System**:
```
Emotional food mapping (categorical + continuous):
  comfort_foods: [list] — Items ordered during stress/sadness
  celebration_foods: [list] — Items ordered during celebrations
  boredom_foods: [list] — Items ordered when bored
  stress_foods: [list] — Items ordered under stress

Current state (dynamic, continuous 0-1):
  stress_level: 0.0-1.0    — Current estimated stress (from recent patterns)
  celebration_level: 0.0-1.0 — Current celebration signal
  boredom_level: 0.0-1.0   — Current variety-seeking signal

Baseline deviation:
  order_frequency_deviation: float — Current vs 30-day average
  aov_deviation: float — Current vs 30-day average
  cuisine_diversity_deviation: float — Current vs 30-day average
```

**MCP Signal Mapping**:
- `get_food_orders` → Order patterns, deviation from baseline, comfort food detection
- `your_go_to_items` → Shifts in go-to items signal emotional change
- `search_restaurants` → Search queries reveal intent ("comfort", "quick", "cheap")
- `get_food_order_details` → Unusual orders (large/small, different cuisine)

**Update Rate**: **Fast** (learning rate: 0.50). Emotions are context-dependent and change rapidly. Use 7-day rolling window for state detection.

**Indian-Specific Considerations**:
- Comfort food varies by region: khichdi (North), curd rice (South), fish curry (Bengal)
- Festival = celebration food (non-negotiable cultural expression)
- Rain → hot fried snacks (pakora, samosa, vada pav) — universal Indian trigger
- Illness → specific foods (khichdi, dal-rice, warm soup)
- "Cheat day" psychology — Indian cheat days are festival-level feasts
- Exam season → student stress eating patterns

---

### Dimension 9: Life Stage

**Definition**: The user's current living situation, household composition, and life context that fundamentally shapes food behavior.

**Psychological Basis**: Developmental psychology and household life-cycle theory. A 23-year-old software engineer living alone in Bengaluru has completely different food needs than a 23-year-old college student in a hostel, even if both "like biryani." Life-stage profiling is the most underappreciated dimension — it should be one of the first things the agent determines.

**Scoring System**:
```
Primary: Categorical (one of 12 profiles)
  life_stage: "college_student" | "young_professional_alone" | "working_professional_roommates" |
              "married_no_kids" | "young_family" | "joint_family" | "nri_remote_ordering" |
              "single_parent" | "senior_citizen" | "fitness_enthusiast" |
              "recently_relocated" | "wfh_professional"

Sub-fields:
  confidence: 0.0-1.0 — Confidence in life-stage classification
  cooking_capability: "none" | "sometimes" | "usually" | "loves_cooking"
  financial_comfort: "tight" | "conscious" | "comfortable" | "premium"
  health_consciousness: "none" | "somewhat" | "focused" | "medical_necessity"

Cross-cutting (continuous 0-1):
  ordering_frequency: float — Orders per week
  avg_order_value: float — ₹ per order
  variety_seeking: 0.0-1.0 — Openness to new items/restaurants
```

**MCP Signal Mapping**:
- `get_food_orders` → Order frequency, value, size, timing patterns
- `get_addresses` → Home/work/travel context, multiple addresses
- `get_booking_status` → Dining out frequency, party size
- `your_go_to_items` → Grocery patterns (cooking capability)
- `search_restaurants` → Search patterns (exploration vs routine)

**Update Rate**: **Slow** (learning rate: 0.05). Life stages are semi-stable but transition detection is critical. Compare last 10 orders vs orders 11-30 for transition signals.

**Indian-Specific Considerations**:
- Joint family is a distinct life stage (not just "family") — multi-generational preferences
- NRI ordering for parents in India is a significant segment
- Hostel/PG living is common for Indian students — distinct from "living alone"
- WFH professionals have unique patterns (lunch peak, afternoon snacks, no commute difference)
- Recently relocated users are a high-frequency, high-exploration segment
- Senior citizens prefer voice-first, simple interfaces — accessibility matters

---

### Dimension 10: Habit Profile

**Definition**: The strength, frequency, and nature of habitual ordering patterns — recurring items, restaurants, timings, and the psychological routines they represent.

**Psychological Basis**: Habit loop theory (Duhigg, 2012). Every habit follows Cue → Routine → Reward. The agent must identify the CUE (time, day, context), understand the ROUTINE (what they order), and recognize the REWARD (why — comfort, celebration, convenience). Research shows Indians tend to order from the same 3-5 restaurants repeatedly (status quo bias is very strong).

**Scoring System**:
```
Habit strength (continuous 0-1):
  overall_habit_strength: 0.0-1.0 — How habitual vs exploratory (recurring items / total items)
  reorder_speed: float — Average seconds to reorder (fast = habitual)
  restaurant_loyalty: 0.0-1.0 — Concentration on top restaurants
  item_loyalty: 0.0-1.0 — Concentration on top items

Specific habits (detected loops):
  recurring_items: [{"item": str, "frequency": str, "strength": 0.0-1.0}]
  recurring_restaurants: [{"name": str, "frequency": str, "strength": 0.0-1.0}]
  temporal_habits: [{"cue": str, "routine": str, "reward": str, "strength": 0.0-1.0}]
  # Examples: "friday_biryani", "morning_dosa", "rain_pakora", "exam_comfort_food"

Derived:
  variety_seeking: 0.0-1.0 — 1 - habit_strength (inverse)
  new_item_rate: 0.0-1.0 — Proportion of orders that are new items
  new_restaurant_rate: 0.0-1.0 — Proportion of orders from new restaurants
```

**MCP Signal Mapping**:
- `your_go_to_items` → Directly reveals recurring items, frequency, brand loyalty
- `get_food_orders` → Recurring items, restaurants, timing patterns
- `get_food_order_details` → Reorder detection (same item, same restaurant)
- `search_restaurants` → Search vs reorder ratio (exploration signal)

**Update Rate**: **Very slow** (learning rate: 0.05). Habits are stable by definition. Weekly recalculation of habit strength. New habits form slowly (21-66 days per research).

**Indian-Specific Considerations**:
- "Friday biryani" is a culturally reinforced habit loop (weekend celebration)
- "Rain pakora" is a seasonal environmental trigger (universal across regions)
- Festival food habits are annual (Diwali sweets, Holi gujiya, Onam sadya)
- Restaurant loyalty is very strong — "my usual place" is a powerful anchor
- Status quo bias means the agent should respect "the usual" before suggesting alternatives
- "Morning filter coffee" in South India is a near-universal daily habit

---

## C. Food DNA Vector Structure

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class DietaryType(Enum):
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    NON_VEGETARIAN = "non_vegetarian"
    JAIN = "jain"
    VEGAN = "vegan"

class RegionType(Enum):
    SOUTH_INDIAN = "south_indian"
    NORTH_INDIAN = "north_indian"
    WEST_INDIAN = "west_indian"
    EAST_INDIAN = "east_indian"
    NORTHEAST_INDIAN = "northeast_indian"

class LifeStageType(Enum):
    COLLEGE_STUDENT = "college_student"
    YOUNG_PROFESSIONAL_ALONE = "young_professional_alone"
    WORKING_PROFESSIONAL_ROOMMATES = "working_professional_roommates"
    MARRIED_NO_KIDS = "married_no_kids"
    YOUNG_FAMILY = "young_family"
    JOINT_FAMILY = "joint_family"
    NRI_REMOTE_ORDERING = "nri_remote_ordering"
    SINGLE_PARENT = "single_parent"
    SENIOR_CITIZEN = "senior_citizen"
    FITNESS_ENTHUSIAST = "fitness_enthusiast"
    RECENTLY_RELOCATED = "recently_relocated"
    WFH_PROFESSIONAL = "wfh_professional"

class ChangeStage(Enum):
    PRE_CONTEMPLATION = "pre_contemplation"
    CONTEMPLATION = "contemplation"
    PREPARATION = "preparation"
    ACTION = "action"
    MAINTENANCE = "maintenance"

@dataclass
class DietaryIdentity:
    primary: DietaryType
    strictness: float = 1.0          # 0.0 (flexible) to 1.0 (absolute)
    home_vs_outside: float = 0.0     # 0.0 (same everywhere) to 1.0 (different rules)
    fasting_frequency: float = 0.0   # 0.0 (never) to 1.0 (very frequent)
    halal_required: bool = False
    satvic_preference: float = 0.0   # 0.0 to 1.0

@dataclass
class RegionalIdentity:
    region: RegionType
    state: str = ""                  # e.g., "karnataka", "tamil_nadu"
    cuisine_affinity: dict = field(default_factory=lambda: {
        "south_indian": 0.0, "north_indian": 0.0, "chinese": 0.0,
        "italian": 0.0, "continental": 0.0, "street_food": 0.0,
        "dessert": 0.0, "fast_food": 0.0, "healthy": 0.0, "other": 0.0
    })
    rice_vs_wheat: float = 0.5       # 0.0 (wheat) to 1.0 (rice)
    spice_tolerance: float = 0.5     # 0.0 (mild) to 1.0 (very spicy)
    sweetness_preference: float = 0.3

@dataclass
class TemporalPattern:
    hour_distribution: list = field(default_factory=lambda: [0.0] * 24)
    day_distribution: list = field(default_factory=lambda: [0.0] * 7)
    breakfast_regularity: float = 0.0
    lunch_regularity: float = 0.0
    dinner_regularity: float = 0.0
    late_night_ratio: float = 0.0
    weekend_ratio: float = 0.0
    order_interval_days: float = 3.0
    order_regularity: float = 0.0

@dataclass
class PricePsychology:
    avg_order_value: float = 0.0
    aov_std: float = 0.0
    price_sensitivity: float = 0.5
    coupon_usage_rate: float = 0.0
    deal_seeking: float = 0.0
    premium_frequency: float = 0.0
    budget_tier: str = "moderate"     # "budget" | "value" | "moderate" | "comfortable" | "premium"
    value_framing: str = "quality"    # "savings" | "quality" | "convenience"

@dataclass
class HealthOrientation:
    health_awareness: float = 0.3
    calorie_awareness: float = 0.2
    health_trend: float = 0.0        # -1.0 (declining) to 1.0 (improving)
    change_stage: ChangeStage = ChangeStage.PRE_CONTEMPLATION
    dietary_goal: str = "none"
    medical_restrictions: list = field(default_factory=list)
    avg_health_score: float = 0.5    # Using IFCT 2017 nutrition data
    healthy_order_ratio: float = 0.3

@dataclass
class SocialDynamics:
    solo_ratio: float = 0.5
    couple_ratio: float = 0.2
    family_ratio: float = 0.2
    group_ratio: float = 0.05
    treat_ratio: float = 0.05
    avg_party_size: float = 1.2
    primary_social_context: str = "solo"
    hospitality_frequency: float = 0.1
    multi_address_ratio: float = 0.1

@dataclass
class EmotionalPatterns:
    comfort_foods: list = field(default_factory=list)
    celebration_foods: list = field(default_factory=list)
    boredom_foods: list = field(default_factory=list)
    stress_foods: list = field(default_factory=list)
    stress_level: float = 0.2        # Current estimated state
    celebration_level: float = 0.0
    boredom_level: float = 0.1

@dataclass
class LifeStageProfile:
    life_stage: LifeStageType = LifeStageType.YOUNG_PROFESSIONAL_ALONE
    confidence: float = 0.0
    cooking_capability: str = "none"   # "none" | "sometimes" | "usually" | "loves_cooking"
    financial_comfort: str = "moderate" # "tight" | "conscious" | "moderate" | "comfortable" | "premium"
    health_consciousness: str = "somewhat" # "none" | "somewhat" | "focused" | "medical_necessity"
    ordering_frequency: float = 4.0    # Orders per week
    variety_seeking: float = 0.3

@dataclass
class HabitProfile:
    overall_habit_strength: float = 0.5
    reorder_speed: float = 120.0       # Seconds to reorder
    restaurant_loyalty: float = 0.5
    item_loyalty: float = 0.5
    recurring_items: list = field(default_factory=list)
    recurring_restaurants: list = field(default_factory=list)
    temporal_habits: list = field(default_factory=list)
    variety_seeking: float = 0.3
    new_item_rate: float = 0.2
    new_restaurant_rate: float = 0.15

@dataclass
class FoodDNA:
    """Complete Food DNA behavioral profile for a user."""
    user_id: str
    version: str = "1.0"
    created_at: str = ""
    last_updated: str = ""

    # 10 Dimensions
    dietary_identity: DietaryIdentity = field(default_factory=DietaryIdentity)
    regional_identity: RegionalIdentity = field(default_factory=RegionalIdentity)
    cuisine_preferences: dict = field(default_factory=dict)
    temporal_pattern: TemporalPattern = field(default_factory=TemporalPattern)
    price_psychology: PricePsychology = field(default_factory=PricePsychology)
    health_orientation: HealthOrientation = field(default_factory=HealthOrientation)
    social_dynamics: SocialDynamics = field(default_factory=SocialDynamics)
    emotional_patterns: EmotionalPatterns = field(default_factory=EmotionalPatterns)
    life_stage: LifeStageProfile = field(default_factory=LifeStageProfile)
    habit_profile: HabitProfile = field(default_factory=HabitProfile)

    # Meta
    data_points: int = 0               # Total orders used to build this profile
    confidence_score: float = 0.0      # Overall profile confidence
    last_major_update: str = ""        # Last time a dimension shifted significantly
```

---

## D. Scoring System

### How Dimensions Combine

Each dimension produces a score or distribution. The Food DNA Vector is a composite that combines them with priority weighting:

```
Priority Order (for recommendation filtering):
  1. Dietary Identity (HARD FILTER — removes non-compliant options entirely)
  2. Regional Identity (strong bias — regional food ranked higher)
  3. Life Stage (baseline expectations — budget, frequency, timing)
  4. Current Context (time, weather, emotional state)
  5. Behavioral Preferences (cuisine, restaurant, items)
  6. Habit Patterns ("your usual" ranked highest for habitual users)
  7. Variety Seeking (occasional new suggestions for exploratory users)
```

### Composite Scoring for Recommendations

```python
def calculate_recommendation_score(item, food_dna, context):
    """Score a food item for recommendation given user's Food DNA and current context."""

    score = 0.0

    # 1. Dietary compliance (HARD FILTER: 0 or 1)
    if not satisfies_dietary(item, food_dna.dietary_identity):
        return 0.0  # Never recommend non-compliant food

    # 2. Regional affinity (weight: 0.20)
    cuisine = item.cuisine_type
    regional_score = food_dna.regional_identity.cuisine_affinity.get(cuisine, 0.1)
    score += regional_score * 0.20

    # 3. Life-stage appropriateness (weight: 0.15)
    life_score = calculate_life_stage_fit(item, food_dna.life_stage, context)
    score += life_score * 0.15

    # 4. Temporal appropriateness (weight: 0.15)
    temporal_score = calculate_temporal_fit(item, food_dna.temporal_pattern, context)
    score += temporal_score * 0.15

    # 5. Price fit (weight: 0.10)
    price_score = calculate_price_fit(item, food_dna.price_psychology)
    score += price_score * 0.10

    # 6. Health alignment (weight: 0.05)
    health_score = calculate_health_fit(item, food_dna.health_orientation)
    score += health_score * 0.05

    # 7. Social fit (weight: 0.05)
    social_score = calculate_social_fit(item, food_dna.social_dynamics, context)
    score += social_score * 0.05

    # 8. Emotional fit (weight: 0.10)
    emotional_score = calculate_emotional_fit(item, food_dna.emotional_patterns, context)
    score += emotional_score * 0.10

    # 9. Habit reinforcement (weight: 0.15)
    habit_score = calculate_habit_fit(item, food_dna.habit_profile, context)
    score += habit_score * 0.15

    # 10. Variety bonus (weight: 0.05)
    variety_score = calculate_variety_bonus(item, food_dna.habit_profile)
    score += variety_score * 0.05

    return score
```

### Confidence Scoring

Confidence determines how much the agent trusts each dimension:

| Data Points | Overall Confidence | Behavior |
|---|---|---|
| 0-2 orders | 0.1-0.2 | Cold start: use location + 1 question only |
| 3-10 orders | 0.3-0.5 | Early profile: dietary + regional emerging |
| 11-30 orders | 0.5-0.7 | Growing profile: most dimensions populated |
| 31-100 orders | 0.7-0.9 | Mature profile: reliable predictions |
| 100+ orders | 0.9-1.0 | Full confidence: cross-server intelligence |

Per-dimension confidence:
```python
dimension_confidence = min(1.0, relevant_data_points / THRESHOLD[dimension])

THRESHOLD = {
    "dietary_identity": 5,      # 5 orders to confirm dietary type
    "regional_identity": 10,    # 10 orders to confirm regional affinity
    "temporal_pattern": 20,     # 20 orders to map time patterns
    "price_psychology": 10,     # 10 orders to estimate price sensitivity
    "health_orientation": 30,   # 30 orders to assess health orientation
    "social_dynamics": 15,      # 15 orders to detect social patterns
    "emotional_patterns": 25,   # 25 orders to detect emotional patterns
    "life_stage": 20,           # 20 orders to classify life stage
    "habit_profile": 30,        # 30 orders to detect habits
}
```

---

## E. MCP Signal Mapping Table

All 35 Swiggy MCP tools mapped to Food DNA dimensions:

| # | MCP Tool | Server | Food DNA Dimensions Informed |
|---|---------|--------|------------------------------|
| 1 | `your_go_to_items` | Instamart | Dietary Identity, Regional Identity, Cuisine Preferences, Habit Profile |
| 2 | `get_food_orders` | Food | All 10 dimensions (primary signal source) |
| 3 | `get_booking_status` | Dineout | Social Dynamics, Price Psychology, Temporal Patterns |
| 4 | `get_addresses` | Shared | Life Stage, Social Dynamics, Regional Identity |
| 5 | `get_food_order_details` | Food | Cuisine Preferences, Price Psychology, Health Orientation, Habit Profile |
| 6 | `get_order_details` | Instamart | Dietary Identity, Health Orientation, Habit Profile |
| 7 | `search_restaurants` | Food | Cuisine Preferences, Price Psychology, Health Orientation |
| 8 | `search_products` | Instamart | Dietary Identity, Health Orientation, Regional Identity |
| 9 | `fetch_food_coupons` | Food | Price Psychology |
| 10 | `apply_food_coupon` | Food | Price Psychology |
| 11 | `get_food_cart` | Food | Emotional Patterns, Price Psychology |
| 12 | `get_cart` | Instamart | Dietary Identity, Health Orientation |
| 13 | `update_food_cart` | Food | Emotional Patterns, Social Dynamics |
| 14 | `update_cart` | Instamart | Dietary Identity, Habit Profile |
| 15 | `clear_food_cart` | Food | Emotional Patterns (decision fatigue) |
| 16 | `clear_cart` | Instamart | Emotional Patterns |
| 17 | `place_food_order` | Food | All dimensions (highest signal) |
| 18 | `place_order` | Instamart | Dietary Identity, Health Orientation, Habit Profile, Price Psychology |
| 19 | `get_restaurant_menu` | Food | Cuisine Preferences, Health Orientation, Price Psychology |
| 20 | `get_product_details` | Instamart | Dietary Identity, Health Orientation |
| 21 | `get_similar_products` | Instamart | Cuisine Preferences, Health Orientation |
| 22 | `get_recommendations` | Instamart | Dietary Identity, Habit Profile, Health Orientation |
| 23 | `get_available_slots` | Instamart | Temporal Patterns, Life Stage |
| 24 | `get_dineout_restaurants` | Dineout | Social Dynamics, Regional Identity, Price Psychology |
| 25 | `get_dineout_restaurant_details` | Dineout | Social Dynamics, Cuisine Preferences |
| 26 | `get_dineout_restaurant_menu` | Dineout | Cuisine Preferences, Health Orientation |
| 27 | `book_restaurant` | Dineout | Social Dynamics, Temporal Patterns, Price Psychology |
| 28 | `cancel_booking` | Dineout | Emotional Patterns |
| 29 | `search_dineout_restaurants` | Dineout | Social Dynamics, Cuisine Preferences |
| 30 | `get_dineout_offers` | Dineout | Price Psychology |
| 31 | `get_food_offers` | Food | Price Psychology |
| 32 | `track_food_order` | Food | Emotional Patterns (anxiety/anticipation) |
| 33 | `cancel_food_order` | Food | Emotional Patterns, Price Psychology |
| 34 | `get_food_delivery_time` | Food | Temporal Patterns, Life Stage |
| 35 | `get_instamart_delivery_time` | Instamart | Temporal Patterns, Life Stage |

---

## F. Sample Food DNA Profiles

### Profile 1: South Indian IT Professional

**Background**: Arjun, 28, software engineer at a Bengaluru startup. Originally from Chennai, moved to Bengaluru 3 years ago. Lives alone in a rented apartment in Koramangala. Vegetarian (family tradition, not strict — eats egg outside). Orders 5-6 times a week. Uses Swiggy One.

**Food DNA Scores**:

| Dimension | Score | Notes |
|---|---|---|
| Dietary Identity | vegetarian, strictness=0.7, home_vs_outside=0.3 | Eggetarian outside home |
| Regional Identity | south_indian (tamil_nadu), rice_vs_wheat=0.85, spice=0.7 | Strong South Indian affinity |
| Cuisine Preferences | south_indian=0.50, chinese=0.20, north_indian=0.15, italian=0.10, other=0.05 | Explores but defaults South |
| Temporal Patterns | breakfast=8AM, lunch=1PM, dinner=9PM, late_night=0.15, weekend=0.35 | Late-night ordering on stressful weeks |
| Price Psychology | AOV=₹280, sensitivity=0.55, coupon_rate=0.40, tier="moderate" | Deals appreciated, not obsessed |
| Health Orientation | awareness=0.45, trend=0.0, stage="contemplation", goal="general_wellness" | Thinking about eating better |
| Social Dynamics | solo=0.70, couple=0.15, family=0.10, group=0.05 | Mostly solo, occasional dates |
| Emotional Patterns | comfort=["Curd Rice", "Sambar Rice", "Dal Rice"], celebration=["Biryani", "Pizza"] | Curd rice = stress food |
| Life Stage | young_professional_alone, cooking="none", financial="comfortable" | Can't cook, decent salary |
| Habit Profile | strength=0.60, friday_biryani=True, morning_dosa=True, restaurant_loyalty=0.65 | Strong routines |

**Sample MCP Signals**:
- `get_food_orders`: 67 orders in 30 days, top restaurant "Saravana Bhavan" (18 orders), top item "Masala Dosa" (12 orders), Friday dinner biryani pattern (4 consecutive Fridays)
- `your_go_to_items`: "Amul Toned Milk 500ml" (every 3 days), "Nandini Curd 400ml" (every 4 days), "MTR Idli Mix" (weekly)
- `get_addresses`: Primary "Koramangala flat", secondary "HSR Layout office"
- `fetch_food_coupons`: Uses 40% of available coupons, prefers free delivery

**Agent Recommendations**:
- Friday 7 PM: "Your usual Friday biryani from Meghana Foods? Or want to try the new Hyderabadi place in Koramangala?" (habit + gentle variety)
- Rainy evening: "It's raining in Koramangala! Perfect for hot pakora from Chaat Street." (environmental trigger)
- After stressful week: "Tough week? Your comfort curd rice from Saravana Bhavan?" (emotional detection)
- Weekend morning: "Sunday breakfast! Your usual masala dosa, or want to try the filter coffee combo?" (habit reinforcement)

---

### Profile 2: North Indian Joint Family

**Background**: Priya, 45, homemaker in Dwarka, Delhi. Joint family of 5: husband (48), two children (16, 12), mother-in-law (72). Orders 2-3 times a week (home cooking is primary). Non-vegetarian (husband and children eat non-veg, mother-in-law is vegetarian). Hosts guests frequently.

**Food DNA Scores**:

| Dimension | Score | Notes |
|---|---|---|
| Dietary Identity | non_vegetarian (mixed household), strictness=0.5, home_vs_outside=0.2 | MIL is veg — needs veg options always |
| Regional Identity | north_indian (delhi/punjab), rice_vs_wheat=0.25, spice=0.8, sweet=0.4 | Wheat-dominant, high spice tolerance |
| Cuisine Preferences | north_indian=0.55, mughlai=0.20, chinese=0.10, south_indian=0.08, other=0.07 | Mughlai for special occasions |
| Temporal Patterns | breakfast=8AM, lunch=1PM, dinner=8PM, late_night=0.02, weekend=0.45 | Weekend = family ordering |
| Price Psychology | AOV=₹650, sensitivity=0.40, coupon_rate=0.25, tier="comfortable" | Family-sized orders, less price-focused |
| Health Orientation | awareness=0.50, trend=0.1, stage="contemplation", medical=["diabetic_mil"] | MIL has diabetes — needs low-sugar options |
| Social Dynamics | solo=0.05, family=0.70, group=0.15, treat=0.10, hospitality=0.25 | Family meals dominate, hosts often |
| Emotional Patterns | comfort=["Rajma Chawal", "Kadhi Chawal"], celebration=["Biryani", "Butter Chicken", "Paneer Tikka"] | Rajma = home comfort |
| Life Stage | joint_family, cooking="usually", financial="comfortable" | Cooks daily, orders for variety/special occasions |
| Habit Profile | strength=0.40, sunday_biryani=True, restaurant_loyalty=0.50 | Moderate habits, variety on weekends |

**Sample MCP Signals**:
- `get_food_orders`: 28 orders in 30 days, average 4.2 items per order, ₹650 AOV, top restaurant "Karim's" (6 orders), Sunday dinner ordering spike
- `get_booking_status`: 3 Dineout bookings in 30 days, family dinners, party size 5-8
- `get_addresses`: Primary "Dwarka Sector 7 home", secondary "Noida relative's home"
- `search_restaurants`: Searches for "family restaurant", "kid friendly", "vegetarian options"

**Agent Recommendations**:
- Sunday 6 PM: "Family Sunday dinner? How about Karim's biryani — mutton for the kids, chicken for you and Papa ji, and paneer tikka for Mummy ji?" (multi-diet family optimization)
- Hosting guests: "Expecting guests? Here's a spread: biryani, butter chicken, dal makhani, naan — party pack for 8 at ₹1,800." (hospitality sizing)
- Kid's exam week: "Kids studying hard? Quick comfort dinner — rajma chawal from Haldiram's, delivered in 30 minutes." (family emotional awareness)
- Mother-in-law's diabetes: "For Mummy ji: sugar-free kheer and low-GI options from Sattviko." (medical dietary filtering)

---

### Profile 3: Bengali College Student

**Background**: Riya, 21, second-year student at Jadavpur University, Kolkata. Lives in a hostel. Eggetarian (eats egg, no meat/fish — personal choice, not family mandate). Budget is tight (₹150-200 per order). Orders 5-6 times a week because hostel food is terrible. Studies late, orders at midnight during exams.

**Food DNA Scores**:

| Dimension | Score | Notes |
|---|---|---|
| Dietary Identity | eggetarian, strictness=0.6, home_vs_outside=0.4 | Eats egg freely, considering non-veg |
| Regional Identity | east_indian (bengal), rice_vs_wheat=0.80, spice=0.6, sweet=0.7 | Bengali sweet tooth |
| Cuisine Preferences | street_food=0.30, chinese=0.25, north_indian=0.20, south_indian=0.10, other=0.15 | Street food and Chinese dominate |
| Temporal Patterns | breakfast=skipped, lunch=1PM, dinner=9PM, late_night=0.35, weekend=0.50 | Heavy late-night ordering during exams |
| Price Psychology | AOV=₹160, sensitivity=0.85, coupon_rate=0.70, tier="budget" | Very price-sensitive, deal-hunter |
| Health Orientation | awareness=0.20, trend=-0.1, stage="pre_contemplation", goal="none" | Health not a priority |
| Social Dynamics | solo=0.30, group=0.55, couple=0.10, treat=0.05 | Group ordering with hostel friends |
| Emotional Patterns | comfort=["Egg Roll", "Maggi", "Chowmein"], celebration=["Pizza", "Biryani"] | Egg roll = hostel comfort food |
| Life Stage | college_student, cooking="none", financial="tight" | Hostel life, zero cooking capability |
| Habit Profile | strength=0.35, variety_seeking=0.65, new_item_rate=0.40 | Exploratory, willing to try new things |

**Sample MCP Signals**:
- `get_food_orders`: 52 orders in 30 days, AOV ₹160, top item "Egg Roll" (9 orders), high late-night ratio (35%), 70% orders with coupons
- `search_restaurants`: Searches for "cheap", "under 150", "hostel delivery", "midnight delivery"
- `get_addresses`: Primary "Jadavpur University Hostel Block B", secondary "Salt Lake home" (holidays)
- `fetch_food_coupons`: Actively searches for and applies every available coupon

**Agent Recommendations**:
- Exam night 11 PM: "Late night study session? Egg roll from Kusum Rolls — ₹60 with coupon, delivered in 20 minutes." (budget + late-night + comfort)
- Group ordering with friends: "Ordering for 4? Combo deal: 4 egg rolls + 2 chowmein = ₹380. Split = ₹95 each." (group budget optimization)
- Weekend treat: "Treating yourself this weekend? Pizza from Domino's — buy 1 get 1 on medium. ₹149 for two!" (celebration within budget)
- Homesick moment: "Missing home? Bengali-style egg curry from Bhojohori Manna — ₹120. Almost like Maa's cooking." (emotional comfort + regional identity)

---

### Profile 4: Gujarati Senior Citizen

**Background**: Mr. Shah, 68, retired bank manager in Ahmedabad. Jain dietary restrictions (no root vegetables, no onion/garlic, no eating after sunset). Lives with wife (64). Children are in the US. Orders 3-4 times a week via voice assistant. Wife has diabetes and mild heart condition.

**Food DNA Scores**:

| Dimension | Score | Notes |
|---|---|---|
| Dietary Identity | jain, strictness=0.95, fasting_frequency=0.40 | Very strict Jain, fasts on Paryushan and Ekadashi |
| Regional Identity | west_indian (gujarat), rice_vs_wheat=0.30, spice=0.4, sweet=0.6 | Gujarati sweet-sour balance |
| Cuisine Preferences | gujarati=0.45, south_indian=0.20, north_indian=0.15, healthy=0.10, other=0.10 | Familiar, traditional preferences |
| Temporal Patterns | breakfast=7AM, lunch=12PM, dinner=6:30PM, late_night=0.0, weekend=0.30 | Early dinner (Jain: no eating after sunset) |
| Price Psychology | AOV=₹220, sensitivity=0.50, coupon_rate=0.15, tier="moderate" | Not price-obsessed but value-conscious |
| Health Orientation | awareness=0.75, trend=0.0, stage="maintenance", medical=["diabetic_wife", "heart_wife"] | High awareness due to wife's conditions |
| Social Dynamics | solo=0.10, couple=0.75, family=0.10, treat=0.05 | Mostly orders for two (couple) |
| Emotional Patterns | comfort=["Khichdi", "Dal Rice", "Thepla"], celebration=["Fafda-Jalebi", "Mohanthal"] | Fafda-jalebi = festival joy |
| Life Stage | senior_citizen, cooking="sometimes", financial="comfortable" | Wife cooks sometimes, orders supplement |
| Habit Profile | strength=0.70, restaurant_loyalty=0.80, item_loyalty=0.75 | Very habitual, loyal to trusted restaurants |

**Sample MCP Signals**:
- `get_food_orders`: 24 orders in 30 days, AOV ₹220, top restaurant "Honest" (8 orders), top item "Thepla" (6 orders), zero late-night orders, all orders before 7 PM
- `your_go_to_items`: "Amul Ghee 500ml" (monthly), "Patanjali Atta" (bi-weekly), "Sugar-free Sweets" (weekly)
- `get_addresses`: Primary "Satellite, Ahmedabad home", secondary "US son's address" (NRI ordering context)
- `search_restaurants`: Searches for "Jain food", "no onion no garlic", "pure veg"

**Agent Recommendations**:
- Evening 5:30 PM: "Dinner for two? Thepla and dal from Honest — Jain preparation, no onion-garlic. ₹180." (habit + dietary compliance)
- Festival (Paryushan): "Paryushan special: Jain thali from Shree Thaal — satvic, no root vegetables. ₹250 for two." (religious calendar awareness)
- Wife's health: "For Be ji: sugar-free mohanthal and low-sodium dal. Doctor-approved options from Govinda's." (medical dietary filtering)
- NRI son ordering: "Your son in the US ordered fafda-jalebi for you and Be ji — Diwali surprise! Delivery at 6 PM today." (cross-border family care)

---

## G. Evolution & Learning

### Learning Rates Per Dimension

| Dimension | Learning Rate | Update Trigger | Window | Rationale |
|---|---|---|---|---|
| Dietary Identity | 0.00 | Never (user-set) | N/A | Identity is non-negotiable |
| Regional Identity | 0.02 | Every order | 90-day | Extremely stable, changes over years |
| Cuisine Preferences | 0.10 | Every order | 30-day | Stable but shifts with exposure |
| Temporal Patterns | 0.20 | Every order | 30-day rolling | Shifts with schedule changes |
| Price Psychology | 0.15 | Every order | 30-day | Shifts with income/membership changes |
| Health Orientation | 0.05 | Every order | 90-day | Very stable, changes with life events |
| Social Dynamics | 0.20 | Every order | 30-day | Shifts with life-stage transitions |
| Emotional Patterns | 0.50 | Every session | 7-day rolling | Context-dependent, fast-changing |
| Life Stage | 0.05 | Every 10 orders | 60-day | Semi-stable, transitions are gradual |
| Habit Profile | 0.05 | Weekly recalculation | 60-day | Habits are stable by definition |

### Update Formula

```python
def update_dimension(current, observation, learning_rate):
    """Exponential moving average update for continuous dimensions."""
    return current * (1 - learning_rate) + observation * learning_rate

# Example: Updating cuisine preference
# Current: south_indian = 0.60
# New observation: user ordered Chinese
# Observation vector: {"south_indian": 0, "chinese": 1, ...}
# Updated: south_indian = 0.60 * 0.90 + 0 * 0.10 = 0.54
#          chinese = 0.10 * 0.90 + 1 * 0.10 = 0.19
```

### Life-Stage Transitions

The agent monitors for life-stage transitions by comparing recent behavior (last 10 orders) against established patterns (orders 11-30):

| Signal | Detected Change | Likely Transition |
|---|---|---|
| Order size increases 50%+, value increases 30%+ | More people eating | Single → Relationship / Family |
| Order frequency drops 40%+ | Less reliance on delivery | Alone → Living with partner (cooking together) |
| Kid-friendly items appear consistently | Children in household | Couple → Parent |
| Health items spike, medical searches appear | Health event | Any → Health-conscious / Medical necessity |
| Late-night ratio drops to near zero | Changed schedule | Student → Professional / Young → Senior |
| New address added, high frequency | Relocated | Recently relocated life stage |
| Coupon usage drops sharply | Income increase | Student → Professional |
| Multiple addresses, timezone mismatch | Remote ordering | Any → NRI remote ordering |

**Transition confidence**: Require 3+ signals aligning before declaring a transition. Use a "transition buffer" of 10 orders before updating life-stage classification.

### Seasonal & Festival Adjustments

India has 30+ major festivals, each with specific food associations. The agent maintains a festival calendar:

```python
FESTIVAL_CALENDAR = {
    "diwali": {"foods": ["mithai", "namkeen", "dry_fruits"], "duration_days": 5, "price_sensitivity_drop": 0.3},
    "holi": {"foods": ["gujiya", "thandai", "chaat"], "duration_days": 2, "price_sensitivity_drop": 0.2},
    "onam": {"foods": ["sadya", "payasam", "banana_chips"], "duration_days": 1, "price_sensitivity_drop": 0.2},
    "pongal": {"foods": ["pongal", "vada", "payasam"], "duration_days": 3, "price_sensitivity_drop": 0.15},
    "durga_puja": {"foods": ["luchi", "kosha_mangsho", "mishti"], "duration_days": 5, "price_sensitivity_drop": 0.25},
    "ramadan": {"foods": ["iftar_items", "biryani", "haleem"], "duration_days": 30, "temporal_shift": True},
    "navratri": {"foods": ["vrat_food", "sabudana", "kuttu"], "duration_days": 9, "dietary_shift": True},
    "ganesh_chaturthi": {"foods": ["modak", "ladoo"], "duration_days": 10, "price_sensitivity_drop": 0.15},
    "eid": {"foods": ["biryani", "seviyan", "sheer_kurma"], "duration_days": 3, "price_sensitivity_drop": 0.2},
    "christmas": {"foods": ["cake", "plum_cake", "roast"], "duration_days": 3, "price_sensitivity_drop": 0.15},
}
```

**Seasonal adjustments**:
- Monsoon (Jun-Sep): Comfort food bias increases 40% (pakora, chai, soup)
- Winter (Nov-Feb): Warm food preference increases (soup, gajar ka halwa)
- Summer (Mar-May): Cold beverages, lighter food, ice cream spike
- Regional seasons matter: South India is different from North India

### Anomaly Detection

The agent monitors for anomalies that signal significant life events:

```python
def detect_anomaly(recent_orders, baseline):
    """Detect ordering anomalies that may signal life events."""

    anomalies = []

    # Dietary violation (e.g., vegetarian ordering non-veg)
    if recent_orders.has_dietary_violation(baseline.dietary_identity):
        anomalies.append({
            "type": "dietary_shift",
            "severity": "high",
            "action": "ask_user_confirm",
            "message": "I noticed you ordered non-vegetarian food. Has your dietary preference changed?"
        })

    # Sudden frequency change
    freq_ratio = recent_orders.frequency / baseline.frequency
    if freq_ratio < 0.3 or freq_ratio > 3.0:
        anomalies.append({
            "type": "frequency_anomaly",
            "severity": "medium",
            "action": "observe_and_adapt"
        })

    # Sudden health shift
    if recent_orders.health_score > baseline.health_score + 0.3:
        anomalies.append({
            "type": "health_shift",
            "severity": "medium",
            "action": "support_new_habits"
        })

    # Emotional distress signal
    if recent_orders.comfort_food_ratio > 0.6 and baseline.comfort_food_ratio < 0.3:
        anomalies.append({
            "type": "emotional_distress",
            "severity": "high",
            "action": "serve_emotional_need",
            "tone": "empathetic"
        })

    return anomalies
```

---

## H. Validation Framework

### Test Scenarios

| # | Scenario | Expected Behavior | Metric |
|---|---|---|---|
| 1 | Jain user browses restaurant menu | Filter out all items with onion/garlic/root vegetables | 100% compliance |
| 2 | Vegetarian user searches for "biryani" | Show only veg biryani options | 100% compliance |
| 3 | User has Friday biryani habit, it's Friday 7 PM | Suggest biryani as first option | Habit detection accuracy |
| 4 | User orders comfort food 3 times in a row | Detect stress, switch to empathetic tone | Emotional detection accuracy |
| 5 | User opens app at 10 PM after a weekday | Show 2-3 quick options, not full menu | Cognitive load adaptation |
| 6 | User's order frequency drops 60% in 2 weeks | Detect possible life-stage transition | Transition detection |
| 7 | Diwali is tomorrow | Proactively suggest mithai and festive food | Festival awareness |
| 8 | User searches for "healthy" for first time | Detect contemplation stage, gentle health suggestions | Stage-of-change detection |
| 9 | NRI user orders to Indian address at 3 AM local | Recognize timezone difference, confirm delivery time | Cross-timezone handling |
| 10 | Family of 5 with mixed dietary preferences | Suggest options that satisfy ALL dietary constraints | Multi-diet optimization |

### Accuracy Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Dietary compliance | 100% | Zero non-compliant recommendations |
| Recommendation acceptance | >60% | Accepted / Total suggestions |
| Reorder prediction | >70% | Correctly predicted next item |
| Time-to-order | <60 sec | Average decision time (lower = better model) |
| Habit detection | >80% | Correctly identified recurring patterns |
| Emotional state accuracy | >65% | Validated against self-report surveys |
| Life-stage classification | >85% | Correct classification from behavioral signals |
| Cold start satisfaction | >50% | User satisfaction within first 5 orders |
| Festival prediction | >90% | Correct festival food suggestions |
| Cross-server consistency | >90% | No contradictions between Food/Instamart/Dineout signals |

### Edge Cases

| Edge Case | Handling Strategy |
|---|---|
| User is vegetarian at home, non-veg outside | Model as `home_vs_outside = 0.8`, adjust recommendations based on delivery address |
| User recently became vegan (was vegetarian) | Detect dietary shift anomaly, ask for confirmation, update identity |
| User is fasting (Navratri/Ramadan) | Detect from calendar + ordering pattern pause, suggest vrat/iftar appropriate food |
| User is traveling (different city) | Detect from new address, adjust restaurant recommendations to local options |
| User has food allergies (not in standard categories) | Allow custom restrictions in medical_restrictions field |
| Multiple users on same account (family) | Detect from order pattern diversity, model as household rather than individual |
| User's go-to restaurant closes | Detect from failed orders, suggest similar alternatives (not random ones) |
| User orders for someone else (gift/surprise) | Detect from unusual address + different food preferences, don't update personal profile |
| Cultural food aversion (e.g., beef for Hindu user) | Religious restrictions go beyond dietary identity — add to religious_restriction field |
| User is pregnant (dietary changes) | Detect from health shift + specific food patterns, add medical dietary needs |

### Validation Methodology

1. **Backtesting**: Replay historical order data through Food DNA model, measure prediction accuracy
2. **A/B Testing**: Compare psychology-driven recommendations vs traditional collaborative filtering
3. **User Surveys**: Post-order satisfaction surveys with Food DNA attribution
4. **Expert Review**: Psychology master's evaluation of behavioral model accuracy
5. **Cross-Cultural Validation**: Test model across 5 regions (South, North, West, East, Northeast)
6. **Cold-Start Testing**: Validate first-5-order experience with new users
7. **Transition Testing**: Validate life-stage transition detection with longitudinal data
8. **Edge-Case Testing**: Specific test suite for all edge cases listed above

---

## References

1. Duhigg, C. (2012). "The Power of Habit." — Habit Loop framework
2. Fogg, B.J. (2020). "Tiny Habits." — Behavior = Motivation × Ability × Prompt
3. Thaler, R.H. & Sunstein, C.R. (2008). "Nudge." — Choice architecture
4. Deci, E.L. & Ryan, R.M. (2000). Self-Determination Theory — Autonomy, competence, relatedness
5. Prochaska, J.O. & DiClemente, C.C. (1983). Transtheoretical Model — Stages of change
6. Michie, S. et al. (2011). COM-B Model — Capability, Opportunity, Motivation
7. Pew Research Center (2021). "Views of religion and food in India."
8. Hungund, S. (2025). "The Role of Food Delivery Apps in Transforming Urban Eating Patterns." medRxiv.
9. IFCT 2017 — Indian Food Composition Tables, National Institute of Nutrition, Hyderabad
10. Kahneman, D. (2011). "Thinking, Fast and Slow." — Peak-end rule, anchoring
