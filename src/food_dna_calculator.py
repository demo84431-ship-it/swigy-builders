"""
Food DNA Agent — Food DNA Calculator

Builds and updates the Food DNA profile from extracted features using
exponential moving average (EMA) updates. Handles confidence scoring
and per-dimension learning rates.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from .food_dna import (
    CONFIDENCE_THRESHOLDS,
    LEARNING_RATES,
    ChangeStage,
    DietaryIdentity,
    DietaryType,
    EmotionalPatterns,
    FoodDNA,
    HabitProfile,
    HealthOrientation,
    LifeStageProfile,
    LifeStageType,
    PricePsychology,
    RegionType,
    RegionalIdentity,
    SocialDynamics,
    TemporalPattern,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EMA helpers
# ---------------------------------------------------------------------------

def ema_scalar(current: float, observation: float, learning_rate: float) -> float:
    """Exponential moving average update for a single scalar."""
    return current * (1 - learning_rate) + observation * learning_rate


def ema_vector(current: list[float], observation: list[float], learning_rate: float) -> list[float]:
    """EMA update for a vector (e.g., hour_distribution)."""
    if len(current) != len(observation):
        logger.warning("Vector length mismatch: %d vs %d", len(current), len(observation))
        return current
    return [c * (1 - learning_rate) + o * learning_rate for c, o in zip(current, observation)]


def ema_dict(current: dict[str, float], observation: dict[str, float], learning_rate: float) -> dict[str, float]:
    """EMA update for a dict distribution."""
    keys = set(current.keys()) | set(observation.keys())
    return {
        k: current.get(k, 0.0) * (1 - learning_rate) + observation.get(k, 0.0) * learning_rate
        for k in keys
    }


# ---------------------------------------------------------------------------
# Confidence calculator
# ---------------------------------------------------------------------------

def calculate_confidence(dimension: str, relevant_data_points: int) -> float:
    """Calculate per-dimension confidence from data point count.

    More data = higher confidence, capped at 1.0.
    Thresholds from the taxonomy (01-food-dna-taxonomy.md §D).
    """
    threshold = CONFIDENCE_THRESHOLDS.get(dimension, 20)
    return min(1.0, relevant_data_points / threshold)


def calculate_overall_confidence(data_points: int) -> float:
    """Overall profile confidence based on total data points."""
    if data_points <= 2:
        return 0.1
    if data_points <= 10:
        return 0.3
    if data_points <= 30:
        return 0.5
    if data_points <= 100:
        return 0.7
    return min(1.0, 0.9 + (data_points - 100) / 1000)


# ---------------------------------------------------------------------------
# Dietary identity inference
# ---------------------------------------------------------------------------

def infer_dietary_type(features: dict[str, Any]) -> DietaryType:
    """Infer dietary type from order signals.

    Uses non_veg_ratio from feature extraction:
    - < 0.05 → vegetarian
    - 0.05–0.3 → eggetarian (egg is common in India)
    - > 0.3 → non_vegetarian
    """
    non_veg_ratio = features.get("non_veg_ratio", 0.0)
    grocery_non_veg = features.get("grocery_non_veg_ratio", 0.0)
    combined = max(non_veg_ratio, grocery_non_veg)

    if combined < 0.05:
        return DietaryType.VEGETARIAN
    if combined < 0.3:
        return DietaryType.EGGETARIAN
    return DietaryType.NON_VEGETARIAN


# ---------------------------------------------------------------------------
# Life stage inference
# ---------------------------------------------------------------------------

def infer_life_stage(features: dict[str, Any]) -> tuple[LifeStageType, float]:
    """Infer life stage from behavioral signals.

    Returns (life_stage, confidence).
    """
    avg_items = features.get("avg_items_per_order", 1)
    avg_aov = features.get("avg_order_value", 200)
    order_count = features.get("order_count", 0)
    has_work = features.get("has_work", False)
    has_home = features.get("has_home", False)
    avg_party = features.get("avg_party_size", 1)

    # Student: low AOV, high frequency, single item orders
    if avg_aov < 200 and order_count > 15:
        return LifeStageType.COLLEGE_STUDENT, 0.5

    # Family: large orders, multiple items
    if avg_items >= 3 or avg_party >= 3:
        return LifeStageType.YOUNG_FAMILY, 0.4

    # Working professional: has work address, moderate AOV
    if has_work:
        return LifeStageType.YOUNG_PROFESSIONAL_ALONE, 0.5

    # Default
    return LifeStageType.YOUNG_PROFESSIONAL_ALONE, 0.2


# ---------------------------------------------------------------------------
# Habit detection
# ---------------------------------------------------------------------------

def detect_habits(features: dict[str, Any]) -> dict[str, Any]:
    """Detect recurring patterns (habit loops) from features.

    Habit loop: Cue → Routine → Reward (Duhigg, 2012).
    We identify cues (time, day), routines (items, restaurants), and
    infer rewards from context.
    """
    habits: dict[str, Any] = {
        "recurring_items": [],
        "recurring_restaurants": [],
        "temporal_habits": [],
    }

    # Recurring items (ordered 3+ times)
    top_items = features.get("top_items", [])
    item_concentration = features.get("item_concentration", 0.0)
    if item_concentration > 0.15:  # High concentration = habitual
        for item in top_items[:5]:
            habits["recurring_items"].append({
                "item": item,
                "strength": min(1.0, item_concentration * 2),
            })

    # Recurring restaurants
    top_restaurants = features.get("top_restaurants", [])
    rest_concentration = features.get("restaurant_concentration", 0.0)
    if rest_concentration > 0.2:
        for rest in top_restaurants[:3]:
            habits["recurring_restaurants"].append({
                "name": rest,
                "strength": min(1.0, rest_concentration * 1.5),
            })

    # Temporal habits: detect day-of-week patterns
    day_dist = features.get("day_distribution", [0.0] * 7)
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, ratio in enumerate(day_dist):
        if ratio > 0.2:  # >20% of orders on this day
            habits["temporal_habits"].append({
                "cue": day_names[i],
                "strength": min(1.0, ratio * 2),
            })

    return habits


# ---------------------------------------------------------------------------
# Main calculator
# ---------------------------------------------------------------------------

class FoodDNACalculator:
    """Builds and updates a Food DNA profile from extracted features.

    Usage:
        calc = FoodDNACalculator()
        dna = calc.build_from_features(features, user_id="user_123")
        # Later, with new signals:
        dna = calc.update(dna, new_features)
    """

    def build_from_features(self, features: dict[str, Any], user_id: str = "") -> FoodDNA:
        """Create a new Food DNA profile from extracted features (cold start).

        On first interaction, only dietary identity and regional identity are
        inferred. Each subsequent update() call adds signal.
        """
        now = datetime.now(timezone.utc).isoformat()
        dna = FoodDNA(user_id=user_id, created_at=now, last_updated=now, data_points=1)

        # Dietary identity (set from first signals)
        dietary_type = infer_dietary_type(features)
        dna.dietary_identity = DietaryIdentity(primary=dietary_type)

        # Regional identity (from cuisine distribution)
        cuisine_dist = features.get("cuisine_distribution", {})
        if cuisine_dist:
            top_cuisine = max(cuisine_dist, key=cuisine_dist.get)
            region_map = {
                "south_indian": RegionType.SOUTH_INDIAN,
                "north_indian": RegionType.NORTH_INDIAN,
                "chinese": RegionType.WEST_INDIAN,  # Chinese is cross-regional
                "street_food": RegionType.NORTH_INDIAN,
            }
            dna.regional_identity = RegionalIdentity(
                region=region_map.get(top_cuisine, RegionType.SOUTH_INDIAN),
                cuisine_affinity=cuisine_dist,
            )

        # Cuisine preferences
        if cuisine_dist:
            dna.cuisine_preferences = dict(cuisine_dist)

        # Temporal patterns
        hour_dist = features.get("hour_distribution", [0.0] * 24)
        day_dist = features.get("day_distribution", [0.0] * 7)
        dna.temporal_pattern = TemporalPattern(
            hour_distribution=hour_dist,
            day_distribution=day_dist,
            late_night_ratio=features.get("late_night_ratio", 0.0),
            weekend_ratio=features.get("weekend_ratio", 0.0),
            order_interval_days=features.get("order_interval_days", 3.0),
        )

        # Price psychology
        avg_aov = features.get("avg_order_value", 0.0)
        aov_std = features.get("aov_std", 0.0)
        if avg_aov > 0:
            # Classify budget tier
            if avg_aov < 150:
                tier = "budget"
            elif avg_aov < 250:
                tier = "value"
            elif avg_aov < 400:
                tier = "moderate"
            elif avg_aov < 600:
                tier = "comfortable"
            else:
                tier = "premium"
            dna.price_psychology = PricePsychology(
                avg_order_value=avg_aov,
                aov_std=aov_std,
                budget_tier=tier,
            )

        # Social dynamics
        avg_items = features.get("avg_items_per_order", 1)
        avg_party = features.get("avg_party_size", 1.0)
        if avg_items >= 3 or avg_party >= 3:
            dna.social_dynamics = SocialDynamics(
                family_ratio=0.6,
                solo_ratio=0.1,
                avg_party_size=max(avg_items, avg_party),
                primary_social_context="family",
            )

        # Health orientation
        grocery_health = features.get("grocery_health_score", 0.5)
        dna.health_orientation = HealthOrientation(
            health_awareness=grocery_health,
            avg_health_score=grocery_health,
        )

        # Life stage
        life_stage, confidence = infer_life_stage(features)
        dna.life_stage = LifeStageProfile(
            life_stage=life_stage,
            confidence=confidence,
        )

        # Habit profile
        habits = detect_habits(features)
        item_conc = features.get("item_concentration", 0.0)
        rest_conc = features.get("restaurant_concentration", 0.0)
        dna.habit_profile = HabitProfile(
            overall_habit_strength=(item_conc + rest_conc) / 2,
            restaurant_loyalty=rest_conc,
            item_loyalty=item_conc,
            recurring_items=habits["recurring_items"],
            recurring_restaurants=habits["recurring_restaurants"],
            temporal_habits=habits["temporal_habits"],
            variety_seeking=1.0 - ((item_conc + rest_conc) / 2),
        )

        # Confidence
        dna.confidence_score = calculate_overall_confidence(1)

        return dna

    def update(self, dna: FoodDNA, features: dict[str, Any]) -> FoodDNA:
        """Update an existing Food DNA profile with new signals.

        Uses exponential moving average with per-dimension learning rates.
        """
        lr = LEARNING_RATES

        # Dietary identity: set once, rarely changes (lr=0.00)
        # Only update if we have enough data to be confident
        if dna.data_points < 5:
            inferred = infer_dietary_type(features)
            if inferred != dna.dietary_identity.primary:
                # Check if the signal is strong enough to change
                non_veg = features.get("non_veg_ratio", 0.0)
                if non_veg > 0.5:
                    dna.dietary_identity.primary = inferred

        # Regional identity: very slow (lr=0.02)
        cuisine_dist = features.get("cuisine_distribution", {})
        if cuisine_dist:
            dna.regional_identity.cuisine_affinity = ema_dict(
                dna.regional_identity.cuisine_affinity, cuisine_dist, lr["regional_identity"]
            )

        # Cuisine preferences: slow (lr=0.10)
        if cuisine_dist:
            dna.cuisine_preferences = ema_dict(
                dna.cuisine_preferences, cuisine_dist, lr["cuisine_preferences"]
            )

        # Temporal patterns: medium (lr=0.20)
        hour_dist = features.get("hour_distribution")
        if hour_dist and len(hour_dist) == 24:
            dna.temporal_pattern.hour_distribution = ema_vector(
                dna.temporal_pattern.hour_distribution, hour_dist, lr["temporal_pattern"]
            )
        day_dist = features.get("day_distribution")
        if day_dist and len(day_dist) == 7:
            dna.temporal_pattern.day_distribution = ema_vector(
                dna.temporal_pattern.day_distribution, day_dist, lr["temporal_pattern"]
            )
        if "late_night_ratio" in features:
            dna.temporal_pattern.late_night_ratio = ema_scalar(
                dna.temporal_pattern.late_night_ratio, features["late_night_ratio"], lr["temporal_pattern"]
            )
        if "weekend_ratio" in features:
            dna.temporal_pattern.weekend_ratio = ema_scalar(
                dna.temporal_pattern.weekend_ratio, features["weekend_ratio"], lr["temporal_pattern"]
            )
        if "order_interval_days" in features:
            dna.temporal_pattern.order_interval_days = ema_scalar(
                dna.temporal_pattern.order_interval_days, features["order_interval_days"], lr["temporal_pattern"]
            )

        # Price psychology: medium (lr=0.15)
        if "avg_order_value" in features:
            dna.price_psychology.avg_order_value = ema_scalar(
                dna.price_psychology.avg_order_value, features["avg_order_value"], lr["price_psychology"]
            )
            # Reclassify budget tier
            aov = dna.price_psychology.avg_order_value
            if aov < 150:
                dna.price_psychology.budget_tier = "budget"
            elif aov < 250:
                dna.price_psychology.budget_tier = "value"
            elif aov < 400:
                dna.price_psychology.budget_tier = "moderate"
            elif aov < 600:
                dna.price_psychology.budget_tier = "comfortable"
            else:
                dna.price_psychology.budget_tier = "premium"

        # Health orientation: very slow (lr=0.05)
        if "grocery_health_score" in features:
            dna.health_orientation.health_awareness = ema_scalar(
                dna.health_orientation.health_awareness, features["grocery_health_score"], lr["health_orientation"]
            )

        # Social dynamics: medium (lr=0.20)
        if "avg_party_size" in features:
            dna.social_dynamics.avg_party_size = ema_scalar(
                dna.social_dynamics.avg_party_size, features["avg_party_size"], lr["social_dynamics"]
            )

        # Emotional patterns: fast (lr=0.50)
        # Detect stress from ordering deviations
        if "order_count" in features and dna.data_points > 10:
            expected_interval = dna.temporal_pattern.order_interval_days
            actual_interval = features.get("order_interval_days", expected_interval)
            if actual_interval < expected_interval * 0.5:
                # Ordering much more frequently than usual → stress eating
                dna.emotional_patterns.stress_level = ema_scalar(
                    dna.emotional_patterns.stress_level, 0.7, lr["emotional_patterns"]
                )
            elif actual_interval > expected_interval * 1.5:
                # Ordering much less → possibly traveling or changed routine
                dna.emotional_patterns.stress_level = ema_scalar(
                    dna.emotional_patterns.stress_level, 0.1, lr["emotional_patterns"]
                )

        # Life stage: very slow (lr=0.05)
        life_stage, confidence = infer_life_stage(features)
        if confidence > dna.life_stage.confidence:
            dna.life_stage.life_stage = life_stage
            dna.life_stage.confidence = confidence

        # Habit profile: very slow (lr=0.05)
        habits = detect_habits(features)
        item_conc = features.get("item_concentration", 0.0)
        rest_conc = features.get("restaurant_concentration", 0.0)
        dna.habit_profile.overall_habit_strength = ema_scalar(
            dna.habit_profile.overall_habit_strength, (item_conc + rest_conc) / 2, lr["habit_profile"]
        )
        dna.habit_profile.restaurant_loyalty = ema_scalar(
            dna.habit_profile.restaurant_loyalty, rest_conc, lr["habit_profile"]
        )
        dna.habit_profile.item_loyalty = ema_scalar(
            dna.habit_profile.item_loyalty, item_conc, lr["habit_profile"]
        )
        # Update recurring items/restaurants if new data is stronger
        if habits["recurring_items"]:
            dna.habit_profile.recurring_items = habits["recurring_items"]
        if habits["recurring_restaurants"]:
            dna.habit_profile.recurring_restaurants = habits["recurring_restaurants"]

        # Meta
        dna.data_points += 1
        dna.confidence_score = calculate_overall_confidence(dna.data_points)
        dna.last_updated = datetime.now(timezone.utc).isoformat()

        return dna
