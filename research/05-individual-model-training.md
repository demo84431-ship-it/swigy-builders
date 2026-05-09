# Individual-Level Model Training Methodology

> **For**: Food DNA Agent (Swiggy Builders Club)
> **Date**: 2026-05-09
> **Purpose**: How to train personalized models for each user from their MCP ordering data

---

## Core Concept: Per-User Behavioral Models

Traditional recommendation systems use **global models** (one model for all users). The Food DNA Agent uses **per-user models** — each user gets their own behavioral model that learns from their specific ordering patterns, psychological profile, and contextual preferences.

**Why per-user models:**
- Indian food behavior is deeply personal (regional, religious, familial)
- Two users in the same city can have completely different food identities
- Global models average out individual patterns; per-user models capture them
- Psychology is individual — emotional triggers, habit loops, and social contexts differ

---

## 1. Data Collection from MCP Signals

### What We Get from Each MCP Tool

| MCP Tool | Data Available | Update Frequency | Psychological Value |
|----------|---------------|------------------|-------------------|
| `your_go_to_items` (Instamart) | Item names, order dates, quantities, spinIds | Per session | Habit patterns, brand loyalty, consumption rate |
| `get_food_orders` (Food) | Restaurant names, items, timestamps, amounts, status | Per session | Cuisine preferences, restaurant loyalty, temporal patterns |
| `get_booking_status` (Dineout) | Restaurant names, dates, party size, deals | Per session | Social dining patterns, occasion types |
| `get_addresses` (Shared) | Location names, addresses, coordinates | Rarely changes | Life context (home, work, travel) |
| `get_food_order_details` (Food) | Specific order: items, total, delivery time | Per order | Detailed preference signals |
| `get_order_details` (Instamart) | Specific order: items, bill, delivery time | Per order | Grocery consumption patterns |
| `search_restaurants` (Food) | Search queries, results shown, restaurants clicked | Per session | Active intent, curiosity, variety-seeking |
| `search_products` (Instamart) | Search queries, products viewed | Per session | Need-based behavior |
| `fetch_food_coupons` (Food) | Available coupons, which ones used | Per session | Price sensitivity, deal-seeking |
| `get_food_cart` / `get_cart` | Cart contents, total, items added/removed | Per session | Decision-making patterns (what's added then removed) |

### Data Schema for Per-User Model

```python
user_behavioral_data = {
    "user_id": "usr_123",
    "sessions": [
        {
            "timestamp": "2026-05-09T19:30:00+05:30",
            "server": "food",  # food, instamart, dineout
            "actions": [
                {"tool": "search_restaurants", "params": {"query": "biryani"}},
                {"tool": "get_restaurant_menu", "params": {"restaurant_id": "res_456"}},
                {"tool": "update_food_cart", "params": {"items": [...]}},
                {"tool": "place_food_order", "params": {"total": 280}}
            ],
            "context": {
                "time_of_day": "evening",
                "day_of_week": "friday",
                "weather": "clear",
                "address": "home"
            }
        }
    ],
    "go_to_items": [
        {"item": "Amul Toned Milk 500ml", "last_ordered": "2026-05-07", "frequency_days": 3},
        {"item": "Amul Butter 100g", "last_ordered": "2026-05-05", "frequency_days": 7}
    ],
    "food_orders": [
        {"restaurant": "Paradise Biryani", "items": ["Chicken Biryani"], 
         "timestamp": "2026-05-02T20:15:00+05:30", "total": 280, "day": "friday"}
    ]
}
```

---

## 2. Feature Engineering Per User

### Temporal Features (From Order Timestamps)

```python
def extract_temporal_features(food_orders):
    """Extract time-based behavioral features from order history."""
    
    features = {}
    
    # Order hour distribution (24-hour histogram)
    hours = [order['timestamp'].hour for order in food_orders]
    features['peak_order_hour'] = mode(hours)  # Most common hour
    features['order_hour_std'] = np.std(hours)  # How consistent
    
    # Day-of-week distribution
    days = [order['timestamp'].weekday() for order in food_orders]
    features['peak_order_day'] = mode(days)
    features['weekend_ratio'] = sum(1 for d in days if d >= 5) / len(days)
    
    # Order interval (days between orders)
    sorted_orders = sorted(food_orders, key=lambda x: x['timestamp'])
    intervals = [(sorted_orders[i+1]['timestamp'] - sorted_orders[i]['timestamp']).days 
                 for i in range(len(sorted_orders)-1)]
    features['avg_order_interval'] = np.mean(intervals) if intervals else 0
    features['order_regularity'] = 1 - (np.std(intervals) / np.mean(intervals)) if intervals else 0
    
    # Time-to-decision (if available from session data)
    # Lower = habitual, higher = exploratory
    
    return features
```

### Preference Features (From Order Items)

```python
def extract_preference_features(food_orders, ifct_data):
    """Extract cuisine and item preference features."""
    
    features = {}
    
    # Cuisine distribution
    cuisines = [order.get('cuisine') for order in food_orders if order.get('cuisine')]
    features['cuisine_distribution'] = Counter(cuisines)
    features['cuisine_diversity'] = len(set(cuisines)) / len(cuisines) if cuisines else 0
    
    # Restaurant loyalty
    restaurants = [order['restaurant'] for order in food_orders]
    features['unique_restaurants'] = len(set(restaurants))
    features['top_restaurant_concentration'] = Counter(restaurants).most_common(1)[0][1] / len(restaurants)
    
    # Price behavior
    totals = [order['total'] for order in food_orders]
    features['avg_order_value'] = np.mean(totals)
    features['aov_std'] = np.std(totals)
    features['max_order_value'] = max(totals)
    
    # Item diversity
    all_items = [item for order in food_orders for item in order.get('items', [])]
    features['unique_items'] = len(set(all_items))
    features['item_diversity'] = len(set(all_items)) / len(all_items) if all_items else 0
    
    # Health score (using IFCT 2017 nutrition data)
    health_scores = []
    for item in all_items:
        nutrition = ifct_data.lookup(item)
        if nutrition:
            # Score based on calories, protein, fiber, sugar
            health_scores.append(calculate_health_score(nutrition))
    features['avg_health_score'] = np.mean(health_scores) if health_scores else 0.5
    
    return features
```

### Behavioral Features (From Patterns)

```python
def extract_behavioral_features(food_orders, go_to_items):
    """Extract habit and behavioral features."""
    
    features = {}
    
    # Habit strength (recurring items)
    item_counts = Counter([item for order in food_orders for item in order.get('items', [])])
    recurring_items = {item: count for item, count in item_counts.items() if count >= 3}
    features['habit_items'] = list(recurring_items.keys())
    features['habit_strength'] = sum(recurring_items.values()) / sum(item_counts.values())
    
    # Variety-seeking score
    total_items = len([item for order in food_orders for item in order.get('items', [])])
    unique_items = len(set([item for order in food_orders for item in order.get('items', [])]))
    features['variety_seeking'] = unique_items / total_items if total_items else 0
    
    # Coupon usage (price sensitivity)
    orders_with_coupons = sum(1 for order in food_orders if order.get('coupon_used'))
    features['coupon_usage_rate'] = orders_with_coupons / len(food_orders) if food_orders else 0
    
    # Reorder speed (how fast they repeat)
    # Fast reorder = high habit, slow reorder = exploratory
    
    # Go-to item patterns (from Instamart)
    if go_to_items:
        features['grocery_frequency'] = np.mean([item['frequency_days'] for item in go_to_items])
        features['grocery_regularity'] = 1 - np.std([item['frequency_days'] for item in go_to_items]) / features['grocery_frequency']
    
    return features
```

### Social Features (From Addresses and Order Size)

```python
def extract_social_features(food_orders, addresses):
    """Extract social context features."""
    
    features = {}
    
    # Solo vs group ordering
    single_item_orders = sum(1 for order in food_orders if len(order.get('items', [])) == 1)
    features['solo_ratio'] = single_item_orders / len(food_orders) if food_orders else 0
    
    # Multi-address ordering (sending food to others)
    unique_addresses = len(set([order.get('address') for order in food_orders if order.get('address')]))
    features['multi_location_ratio'] = unique_addresses / len(food_orders) if food_orders else 0
    
    # Average party size (estimated from order size)
    estimated_party_sizes = []
    for order in food_orders:
        item_count = len(order.get('items', []))
        total = order.get('total', 0)
        # Heuristic: 1-2 items = 1 person, 3-4 = 2, 5+ = 3+
        estimated_party_sizes.append(max(1, item_count // 2))
    features['avg_party_size'] = np.mean(estimated_party_sizes) if estimated_party_sizes else 1
    
    return features
```

---

## 3. Per-User Model Architecture

### The Food DNA Vector

Each user's behavioral profile is stored as a **Food DNA Vector** — a multi-dimensional representation of their food psychology.

```python
food_dna_vector = {
    # Identity dimensions (stable, rarely change)
    "dietary_identity": "vegetarian",  # veg, non_veg, jain, vegan, eggetarian
    "regional_identity": "south_indian",  # south, north, west, east, northeast
    "religious_restriction": "hindu",  # hindu, muslim, jain, sikh, christian, none
    
    # Behavioral dimensions (learned from data, update over time)
    "cuisine_preferences": {
        "south_indian": 0.65,
        "north_indian": 0.15,
        "chinese": 0.10,
        "italian": 0.05,
        "other": 0.05
    },
    "temporal_pattern": {
        "breakfast_cuisine": "south_indian",
        "lunch_cuisine": "south_indian",
        "dinner_cuisine": "north_indian",
        "peak_breakfast_hour": 8,
        "peak_lunch_hour": 13,
        "peak_dinner_hour": 21
    },
    "price_profile": {
        "avg_order_value": 220,
        "price_sensitivity": 0.7,  # 0 = insensitive, 1 = very sensitive
        "coupon_usage_rate": 0.45,
        "premium_frequency": 0.1  # How often they order premium
    },
    "health_profile": {
        "avg_health_score": 0.55,  # 0 = unhealthy, 1 = healthy
        "health_trend": "stable",  # improving, declining, stable
        "dietary_goal": "none"  # weight_loss, muscle_gain, diabetic, none
    },
    "habit_profile": {
        "habit_strength": 0.65,  # How habitual (0 = exploratory, 1 = very habitual)
        "recurring_items": ["Chicken Biryani", "Masala Dosa", "Filter Coffee"],
        "recurring_restaurants": ["Paradise", "Saravana Bhavan"],
        "friday_biryani": True,  # Specific habit detection
        "morning_dosa": True
    },
    "social_profile": {
        "solo_ratio": 0.6,
        "family_ratio": 0.3,
        "group_ratio": 0.1,
        "primary_address": "home",
        "secondary_addresses": ["work", "friend_rajesh"]
    },
    "emotional_profile": {
        "comfort_foods": ["Khichdi", "Curd Rice", "Dal Rice"],
        "celebration_foods": ["Biryani", "Pizza", "Ice Cream"],
        "stress_indicator": 0.2  # Current stress level (0-1)
    },
    "variety_profile": {
        "variety_seeking": 0.3,  # 0 = always same, 1 = always new
        "new_restaurant_rate": 0.15,
        "new_item_rate": 0.2
    }
}
```

### Model Update Frequency

| Dimension | Update Trigger | Learning Rate |
|-----------|---------------|---------------|
| Dietary identity | Never (user-set) | N/A |
| Regional identity | Rarely (learned from first 10 orders) | Very slow |
| Cuisine preferences | Every order | Slow (exponential moving average) |
| Temporal pattern | Every order | Medium (rolling 30-day window) |
| Price profile | Every order | Medium |
| Health profile | Every order | Slow |
| Habit profile | Weekly recalculation | Slow |
| Social profile | Every order | Medium |
| Emotional profile | Every session | Fast (context-dependent) |
| Variety profile | Every order | Slow |

---

## 4. Cold Start Strategy

### The Problem
New users have no order history. How do we build a useful Food DNA from minimal data?

### Solution: Progressive Profiling

**Session 1 (Zero data):**
```
User opens agent for first time.
→ Ask 1 question: "Are you vegetarian, non-vegetarian, or Jain?"
→ Use answer + location (from address) to infer regional identity
→ Show most popular restaurants in their area
→ Default to "safe" recommendations (popular, well-rated)
```

**Session 2-5 (Minimal data):**
```
User has ordered 1-3 times.
→ Extract: cuisine preference, price range, ordering time
→ Infer: dietary identity confirmation, regional lean
→ Show: similar to what they ordered + 1 "you might also like"
→ Ask: "How was your order?" (feedback loop)
```

**Session 6-20 (Building profile):**
```
User has ordered 5-15 times.
→ Extract: habit patterns, restaurant loyalty, temporal rhythm
→ Detect: recurring items, preferred restaurants
→ Show: "Your usual" + personalized suggestions
→ Build: habit loops, social context
```

**Session 20+ (Mature profile):**
```
User has ordered 15+ times.
→ Full Food DNA available
→ Proactive suggestions, habit-aware, emotion-aware
→ Cross-server intelligence (Food + Instamart + Dineout)
→ Predictive ordering ("Running low on milk?")
```

### Cold Start Data Sources

| Data Source | Available From | What It Tells Us |
|------------|---------------|-----------------|
| Location | First session | Regional identity, cuisine defaults |
| Language | First session | Regional identity, vernacular preference |
| Time of day | First session | Meal timing preference |
| Device type | First session | Tech sophistication, interaction style |
| First order | Session 1 | Cuisine, price range, dietary identity |
| Search queries | Session 1+ | Active intent, curiosity |
| Coupon usage | Session 2+ | Price sensitivity |

---

## 5. Model Training Pipeline

### Step 1: Data Ingestion

```python
class MCPDataCollector:
    """Collects and stores behavioral data from MCP tool calls."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.sessions = []
        self.go_to_items = []
        self.food_orders = []
        self.addresses = []
    
    def record_session(self, session_data):
        """Record a complete MCP session."""
        self.sessions.append(session_data)
        self._update_orders(session_data)
        self._update_go_to_items(session_data)
    
    def _update_orders(self, session):
        """Extract order data from session."""
        for action in session['actions']:
            if action['tool'] == 'place_food_order':
                self.food_orders.append({
                    'timestamp': session['timestamp'],
                    'items': action['params'].get('items', []),
                    'total': action['params'].get('total', 0),
                    'restaurant': action['params'].get('restaurant', ''),
                    'address': session['context'].get('address', ''),
                    'coupon_used': action['params'].get('coupon_applied', False)
                })
```

### Step 2: Feature Extraction

```python
class FeatureExtractor:
    """Extracts psychological features from raw MCP data."""
    
    def __init__(self, ifct_data):
        self.ifct = ifct_data
    
    def extract_all_features(self, user_data):
        """Extract complete feature set for a user."""
        features = {}
        features.update(extract_temporal_features(user_data.food_orders))
        features.update(extract_preference_features(user_data.food_orders, self.ifct))
        features.update(extract_behavioral_features(user_data.food_orders, user_data.go_to_items))
        features.update(extract_social_features(user_data.food_orders, user_data.addresses))
        return features
```

### Step 3: Food DNA Calculation

```python
class FoodDNACalculator:
    """Calculates Food DNA vector from features."""
    
    def calculate(self, features, user_settings):
        """Calculate complete Food DNA from features."""
        dna = {}
        
        # Identity (from user settings + inference)
        dna['dietary_identity'] = user_settings.get('dietary_identity', 
            self._infer_dietary_identity(features))
        dna['regional_identity'] = self._infer_regional_identity(features)
        
        # Preferences (from order history)
        dna['cuisine_preferences'] = self._calculate_cuisine_distribution(features)
        dna['temporal_pattern'] = self._calculate_temporal_pattern(features)
        dna['price_profile'] = self._calculate_price_profile(features)
        
        # Behavioral (from patterns)
        dna['habit_profile'] = self._calculate_habit_profile(features)
        dna['social_profile'] = self._calculate_social_profile(features)
        dna['variety_profile'] = self._calculate_variety_profile(features)
        
        # Health (from IFCT nutrition data)
        dna['health_profile'] = self._calculate_health_profile(features)
        
        return dna
    
    def _infer_dietary_identity(self, features):
        """Infer dietary identity from order history."""
        # If all items are vegetarian → vegetarian
        # If contains chicken/mutton/fish → non-vegetarian
        # If contains egg but no meat → eggetarian
        # Use IFCT food groups for classification
        pass
    
    def _infer_regional_identity(self, features):
        """Infer regional identity from cuisine preferences."""
        cuisine_dist = features.get('cuisine_distribution', {})
        if cuisine_dist.get('south_indian', 0) > 0.5:
            return 'south_indian'
        elif cuisine_dist.get('north_indian', 0) > 0.5:
            return 'north_indian'
        # ... etc
        pass
```

### Step 4: Recommendation Generation

```python
class PsychologyDrivenRecommender:
    """Generates recommendations using Food DNA + psychological principles."""
    
    def __init__(self, food_dna, ifct_data, mcp_client):
        self.dna = food_dna
        self.ifct = ifct_data
        self.mcp = mcp_client
    
    def recommend(self, context):
        """Generate personalized recommendation based on context."""
        
        # Step 1: Determine psychological state
        psych_state = self._assess_psychological_state(context)
        
        # Step 2: Apply appropriate strategy
        if psych_state['fatigue'] > 0.7:
            return self._simple_reorder()  # High fatigue → just reorder
        elif psych_state['emotional_state'] == 'stressed':
            return self._comfort_food_suggestion()  # Stressed → comfort
        elif psych_state['social_context'] == 'family':
            return self._family_suggestion()  # Family → variety
        elif psych_state['variety_seeking'] > 0.7:
            return self._new_restaurant_suggestion()  # Bored → variety
        else:
            return self._personalized_suggestion(context)  # Default
    
    def _assess_psychological_state(self, context):
        """Determine current psychological state from context."""
        state = {}
        
        # Fatigue (from time of day, day of week)
        hour = context.get('hour', 12)
        state['fatigue'] = self._calculate_fatigue(hour, context.get('day', 0))
        
        # Emotional state (from recent ordering patterns)
        state['emotional_state'] = self._detect_emotional_state()
        
        # Social context (from address, order size)
        state['social_context'] = self._detect_social_context(context)
        
        # Variety seeking (from recent order diversity)
        state['variety_seeking'] = self.dna['variety_profile']['variety_seeking']
        
        return state
    
    def _simple_reorder(self):
        """One-tap reorder for high-fatigue moments."""
        top_items = self.dna['habit_profile']['recurring_items'][:3]
        return {
            'type': 'simple_reorder',
            'message': f"Your usual? {top_items[0]} from {self.dna['habit_profile']['recurring_restaurants'][0]}",
            'options': top_items[:3],
            'voice': True  # Voice-optimized response
        }
    
    def _comfort_food_suggestion(self):
        """Comfort food for stressed users."""
        comfort_foods = self.dna['emotional_profile']['comfort_foods']
        return {
            'type': 'comfort',
            'message': "Tough day? Here's some comfort food:",
            'options': comfort_foods[:3],
            'tone': 'empathetic'
        }
```

---

## 6. Feedback Loop & Continuous Learning

### How the Model Improves Over Time

```
User orders → Agent observes → Features update → Food DNA updates → Better recommendations
     ↑                                                                        |
     └────────────────────────────────────────────────────────────────────────┘
                                    Feedback Loop
```

### Feedback Signals

| Signal | Type | Weight | How Captured |
|--------|------|--------|-------------|
| Order completed | Positive | High | `place_food_order` success |
| Order rejected | Negative | High | User says "no" to suggestion |
| Item added then removed | Negative | Medium | Cart analysis |
| Reordered same item | Positive (habit) | Medium | `your_go_to_items` pattern |
| Tried new restaurant | Positive (variety) | Low | New restaurant in history |
| Used coupon | Neutral (price) | Low | `apply_food_coupon` |
| Order cancelled | Negative | High | Order status |
| Quick reorder (< 30 sec) | Positive (habit) | Medium | Session timing |
| Long browsing (> 5 min) | Neutral (exploring) | Low | Session timing |

### Learning Rate by Dimension

```python
# Exponential moving average for preference updates
def update_preference(current_value, new_observation, learning_rate=0.1):
    """Update preference with exponential moving average."""
    return current_value * (1 - learning_rate) + new_observation * learning_rate

# Different learning rates for different dimensions
LEARNING_RATES = {
    'cuisine_preferences': 0.1,   # Slow — preferences are stable
    'temporal_pattern': 0.2,      # Medium — timing can shift
    'price_profile': 0.15,        # Medium — price sensitivity changes
    'health_profile': 0.05,       # Very slow — health orientation is stable
    'habit_profile': 0.05,        # Very slow — habits change slowly
    'social_profile': 0.2,        # Medium — social context changes
    'emotional_profile': 0.5,     # Fast — emotions are context-dependent
    'variety_profile': 0.1,       # Slow — variety-seeking is a trait
}
```

---

## 7. Model Evaluation Metrics

### How to Measure if the Model is Working

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| **Recommendation acceptance rate** | % of suggestions user accepts | >60% |
| **Reorder prediction accuracy** | Correctly predicted next order | >70% |
| **Time-to-order** | How fast user decides (lower = better model) | <60 seconds |
| **Habit detection accuracy** | Correctly identified recurring patterns | >80% |
| **Dietary identity accuracy** | Never suggests violating dietary rules | 100% |
| **Emotional state accuracy** | Correctly detects mood from patterns | >65% |
| **Cold start satisfaction** | User satisfaction with first 5 recommendations | >50% |
| **Long-term retention** | Users still using agent after 30 days | >40% |

---

## Key Takeaways

1. **Per-user models, not global models** — Each user gets their own behavioral model that learns from their specific patterns
2. **Psychological features, not just statistical features** — Extract emotional state, social context, cognitive load, habit strength — not just "what did they order"
3. **Progressive profiling** — Start with 1 question, build up to full Food DNA over 20+ sessions
4. **Psychology-driven recommendations** — Use the right psychological strategy for the right context (comfort when stressed, variety when bored, simple when tired)
5. **Continuous learning** — Every order updates the model, with different learning rates for different dimensions
6. **Identity is non-negotiable** — Dietary, regional, and religious identity constraints are NEVER overridden by the model
