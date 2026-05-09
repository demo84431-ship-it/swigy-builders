"""
Food DNA Agent — Food DNA Data Model

Complete behavioral profile with 10 dimensions matching the taxonomy design.
Each dimension has sub-fields, default values, and confidence scoring.

Based on: design/01-food-dna-taxonomy.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

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
    """Transtheoretical Model stages for health behavior change."""
    PRE_CONTEMPLATION = "pre_contemplation"
    CONTEMPLATION = "contemplation"
    PREPARATION = "preparation"
    ACTION = "action"
    MAINTENANCE = "maintenance"


# ---------------------------------------------------------------------------
# Dimension dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DietaryIdentity:
    """Dimension 1: Fundamental dietary classification (non-negotiable).

    This is the highest-priority dimension — a hard filter that removes
    non-compliant options entirely. Never overridden by the model.
    Psychological basis: Self-affirmation theory (Steele, 1988).
    """
    primary: DietaryType = DietaryType.VEGETARIAN
    strictness: float = 1.0          # 0.0 (flexible) → 1.0 (absolute)
    home_vs_outside: float = 0.0     # 0.0 (same everywhere) → 1.0 (different rules)
    fasting_frequency: float = 0.0   # 0.0 (never) → 1.0 (very frequent)
    halal_required: bool = False
    satvic_preference: float = 0.0   # 0.0 → 1.0


@dataclass
class RegionalIdentity:
    """Dimension 2: Geographic and cultural food identity.

    Extremely stable — changes over years, not weeks.
    Psychological basis: Cultural psychology, identity theory.
    """
    region: RegionType = RegionType.SOUTH_INDIAN
    state: str = ""  # e.g., "karnataka", "tamil_nadu"
    cuisine_affinity: dict[str, float] = field(default_factory=lambda: {
        "south_indian": 0.0, "north_indian": 0.0, "chinese": 0.0,
        "italian": 0.0, "continental": 0.0, "street_food": 0.0,
        "dessert": 0.0, "fast_food": 0.0, "healthy": 0.0, "other": 0.0,
    })
    rice_vs_wheat: float = 0.5       # 0.0 (wheat-dominant) → 1.0 (rice-dominant)
    spice_tolerance: float = 0.5     # 0.0 (mild) → 1.0 (very spicy)
    sweetness_preference: float = 0.3


@dataclass
class TemporalPattern:
    """Dimension 4: Ordering rhythm across time-of-day, day-of-week, and seasons.

    Psychological basis: Chronobiology and habit loop theory.
    Uses 30-day rolling window.
    """
    hour_distribution: list[float] = field(default_factory=lambda: [0.0] * 24)
    day_distribution: list[float] = field(default_factory=lambda: [0.0] * 7)
    breakfast_regularity: float = 0.0
    lunch_regularity: float = 0.0
    dinner_regularity: float = 0.0
    late_night_ratio: float = 0.0
    weekend_ratio: float = 0.0
    order_interval_days: float = 3.0
    order_regularity: float = 0.0


@dataclass
class PricePsychology:
    """Dimension 5: How the user perceives and responds to price.

    Psychological basis: Behavioral economics — anchoring, loss aversion, framing.
    Key insight: Always show original price + discount together.
    """
    avg_order_value: float = 0.0
    aov_std: float = 0.0
    price_sensitivity: float = 0.5
    coupon_usage_rate: float = 0.0
    deal_seeking: float = 0.0
    premium_frequency: float = 0.0
    budget_tier: str = "moderate"     # budget | value | moderate | comfortable | premium
    value_framing: str = "quality"    # savings | quality | convenience


@dataclass
class HealthOrientation:
    """Dimension 6: Relationship with health, nutrition, and dietary goals.

    Psychological basis: Health Belief Model, Transtheoretical Model (Stages of Change).
    Never push health on someone in pre-contemplation — detect the stage first.
    """
    health_awareness: float = 0.3
    calorie_awareness: float = 0.2
    health_trend: float = 0.0        # -1.0 (declining) → 1.0 (improving)
    change_stage: ChangeStage = ChangeStage.PRE_CONTEMPLATION
    dietary_goal: str = "none"       # none | weight_loss | muscle_gain | diabetic | heart_healthy | general_wellness
    medical_restrictions: list[str] = field(default_factory=list)
    avg_health_score: float = 0.5
    healthy_order_ratio: float = 0.3


@dataclass
class SocialDynamics:
    """Dimension 7: Solo, family, group, and hosting food behavior.

    Psychological basis: Social psychology, commensality research.
    In India, the decision unit is often the family, not the individual.
    """
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
    """Dimension 8: How emotional states influence food choices.

    Psychological basis: Emotional eating research.
    Key: NEVER push healthy food on a stressed user — serve the emotional need first.
    Fast-updating (lr=0.50, 7-day rolling window).
    """
    comfort_foods: list[str] = field(default_factory=list)
    celebration_foods: list[str] = field(default_factory=list)
    boredom_foods: list[str] = field(default_factory=list)
    stress_foods: list[str] = field(default_factory=list)
    stress_level: float = 0.2
    celebration_level: float = 0.0
    boredom_level: float = 0.1


@dataclass
class LifeStageProfile:
    """Dimension 9: Living situation, household composition, life context.

    Psychological basis: Developmental psychology, household life-cycle theory.
    A 23-year-old engineer alone ≠ a 23-year-old student in a hostel.
    """
    life_stage: LifeStageType = LifeStageType.YOUNG_PROFESSIONAL_ALONE
    confidence: float = 0.0
    cooking_capability: str = "none"       # none | sometimes | usually | loves_cooking
    financial_comfort: str = "moderate"    # tight | conscious | moderate | comfortable | premium
    health_consciousness: str = "somewhat" # none | somewhat | focused | medical_necessity
    ordering_frequency: float = 4.0        # orders per week
    variety_seeking: float = 0.3


@dataclass
class HabitProfile:
    """Dimension 10: Strength, frequency, and nature of habitual ordering patterns.

    Psychological basis: Habit loop theory (Duhigg, 2012).
    Every habit: Cue → Routine → Reward. The agent identifies all three.
    Very stable (lr=0.05). New habits form in 21-66 days.
    """
    overall_habit_strength: float = 0.5
    reorder_speed: float = 120.0       # seconds to reorder (fast = habitual)
    restaurant_loyalty: float = 0.5
    item_loyalty: float = 0.5
    recurring_items: list[dict[str, Any]] = field(default_factory=list)
    recurring_restaurants: list[dict[str, Any]] = field(default_factory=list)
    temporal_habits: list[dict[str, Any]] = field(default_factory=list)
    variety_seeking: float = 0.3
    new_item_rate: float = 0.2
    new_restaurant_rate: float = 0.15


# ---------------------------------------------------------------------------
# Confidence thresholds per dimension
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLDS: dict[str, int] = {
    "dietary_identity": 5,
    "regional_identity": 10,
    "cuisine_preferences": 10,
    "temporal_pattern": 20,
    "price_psychology": 10,
    "health_orientation": 30,
    "social_dynamics": 15,
    "emotional_patterns": 25,
    "life_stage": 20,
    "habit_profile": 30,
}

# Learning rates per dimension (from taxonomy)
LEARNING_RATES: dict[str, float] = {
    "dietary_identity": 0.00,      # Never updates automatically
    "regional_identity": 0.02,     # Extremely stable
    "cuisine_preferences": 0.10,   # Stable but shifts with exposure
    "temporal_pattern": 0.20,      # Shifts with schedule changes
    "price_psychology": 0.15,      # Shifts with income/membership
    "health_orientation": 0.05,    # Very stable
    "social_dynamics": 0.20,       # Shifts with life-stage transitions
    "emotional_patterns": 0.50,    # Context-dependent, fast-changing
    "life_stage": 0.05,            # Semi-stable
    "habit_profile": 0.05,         # Stable by definition
}


# ---------------------------------------------------------------------------
# Top-level Food DNA profile
# ---------------------------------------------------------------------------

@dataclass
class FoodDNA:
    """Complete Food DNA behavioral profile for a user.

    This is the central data structure of the agent — a multi-dimensional
    psychological fingerprint built from behavioral signals across
    Swiggy's three MCP servers.
    """
    user_id: str = ""
    version: str = "1.0"
    created_at: str = ""
    last_updated: str = ""

    # 10 Dimensions
    dietary_identity: DietaryIdentity = field(default_factory=DietaryIdentity)
    regional_identity: RegionalIdentity = field(default_factory=RegionalIdentity)
    cuisine_preferences: dict[str, float] = field(default_factory=lambda: {
        "south_indian": 0.0, "north_indian": 0.0, "chinese": 0.0,
        "italian": 0.0, "continental": 0.0, "street_food": 0.0,
        "dessert": 0.0, "fast_food": 0.0, "healthy": 0.0, "other": 0.0,
    })
    temporal_pattern: TemporalPattern = field(default_factory=TemporalPattern)
    price_psychology: PricePsychology = field(default_factory=PricePsychology)
    health_orientation: HealthOrientation = field(default_factory=HealthOrientation)
    social_dynamics: SocialDynamics = field(default_factory=SocialDynamics)
    emotional_patterns: EmotionalPatterns = field(default_factory=EmotionalPatterns)
    life_stage: LifeStageProfile = field(default_factory=LifeStageProfile)
    habit_profile: HabitProfile = field(default_factory=HabitProfile)

    # Meta
    data_points: int = 0
    confidence_score: float = 0.0
    last_major_update: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.last_updated:
            self.last_updated = self.created_at

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire Food DNA profile to a dict (JSON-safe)."""
        def _dc(obj: Any) -> Any:
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _dc(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, list):
                return [_dc(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _dc(v) for k, v in obj.items()}
            return obj

        return _dc(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FoodDNA":
        """Deserialize a Food DNA profile from a dict."""
        dna = cls(user_id=data.get("user_id", ""))
        dna.version = data.get("version", "1.0")
        dna.created_at = data.get("created_at", "")
        dna.last_updated = data.get("last_updated", "")
        dna.data_points = data.get("data_points", 0)
        dna.confidence_score = data.get("confidence_score", 0.0)
        dna.last_major_update = data.get("last_major_update", "")

        # Dietary Identity
        di = data.get("dietary_identity", {})
        dna.dietary_identity = DietaryIdentity(
            primary=DietaryType(di.get("primary", "vegetarian")),
            strictness=di.get("strictness", 1.0),
            home_vs_outside=di.get("home_vs_outside", 0.0),
            fasting_frequency=di.get("fasting_frequency", 0.0),
            halal_required=di.get("halal_required", False),
            satvic_preference=di.get("satvic_preference", 0.0),
        )

        # Regional Identity
        ri = data.get("regional_identity", {})
        dna.regional_identity = RegionalIdentity(
            region=RegionType(ri.get("region", "south_indian")),
            state=ri.get("state", ""),
            cuisine_affinity=ri.get("cuisine_affinity", dna.regional_identity.cuisine_affinity),
            rice_vs_wheat=ri.get("rice_vs_wheat", 0.5),
            spice_tolerance=ri.get("spice_tolerance", 0.5),
            sweetness_preference=ri.get("sweetness_preference", 0.3),
        )

        # Cuisine preferences
        dna.cuisine_preferences = data.get("cuisine_preferences", dna.cuisine_preferences)

        # Temporal Pattern
        tp = data.get("temporal_pattern", {})
        dna.temporal_pattern = TemporalPattern(
            hour_distribution=tp.get("hour_distribution", [0.0] * 24),
            day_distribution=tp.get("day_distribution", [0.0] * 7),
            breakfast_regularity=tp.get("breakfast_regularity", 0.0),
            lunch_regularity=tp.get("lunch_regularity", 0.0),
            dinner_regularity=tp.get("dinner_regularity", 0.0),
            late_night_ratio=tp.get("late_night_ratio", 0.0),
            weekend_ratio=tp.get("weekend_ratio", 0.0),
            order_interval_days=tp.get("order_interval_days", 3.0),
            order_regularity=tp.get("order_regularity", 0.0),
        )

        # Price Psychology
        pp = data.get("price_psychology", {})
        dna.price_psychology = PricePsychology(
            avg_order_value=pp.get("avg_order_value", 0.0),
            aov_std=pp.get("aov_std", 0.0),
            price_sensitivity=pp.get("price_sensitivity", 0.5),
            coupon_usage_rate=pp.get("coupon_usage_rate", 0.0),
            deal_seeking=pp.get("deal_seeking", 0.0),
            premium_frequency=pp.get("premium_frequency", 0.0),
            budget_tier=pp.get("budget_tier", "moderate"),
            value_framing=pp.get("value_framing", "quality"),
        )

        # Health Orientation
        ho = data.get("health_orientation", {})
        dna.health_orientation = HealthOrientation(
            health_awareness=ho.get("health_awareness", 0.3),
            calorie_awareness=ho.get("calorie_awareness", 0.2),
            health_trend=ho.get("health_trend", 0.0),
            change_stage=ChangeStage(ho.get("change_stage", "pre_contemplation")),
            dietary_goal=ho.get("dietary_goal", "none"),
            medical_restrictions=ho.get("medical_restrictions", []),
            avg_health_score=ho.get("avg_health_score", 0.5),
            healthy_order_ratio=ho.get("healthy_order_ratio", 0.3),
        )

        # Social Dynamics
        sd = data.get("social_dynamics", {})
        dna.social_dynamics = SocialDynamics(
            solo_ratio=sd.get("solo_ratio", 0.5),
            couple_ratio=sd.get("couple_ratio", 0.2),
            family_ratio=sd.get("family_ratio", 0.2),
            group_ratio=sd.get("group_ratio", 0.05),
            treat_ratio=sd.get("treat_ratio", 0.05),
            avg_party_size=sd.get("avg_party_size", 1.2),
            primary_social_context=sd.get("primary_social_context", "solo"),
            hospitality_frequency=sd.get("hospitality_frequency", 0.1),
            multi_address_ratio=sd.get("multi_address_ratio", 0.1),
        )

        # Emotional Patterns
        ep = data.get("emotional_patterns", {})
        dna.emotional_patterns = EmotionalPatterns(
            comfort_foods=ep.get("comfort_foods", []),
            celebration_foods=ep.get("celebration_foods", []),
            boredom_foods=ep.get("boredom_foods", []),
            stress_foods=ep.get("stress_foods", []),
            stress_level=ep.get("stress_level", 0.2),
            celebration_level=ep.get("celebration_level", 0.0),
            boredom_level=ep.get("boredom_level", 0.1),
        )

        # Life Stage
        ls = data.get("life_stage", {})
        dna.life_stage = LifeStageProfile(
            life_stage=LifeStageType(ls.get("life_stage", "young_professional_alone")),
            confidence=ls.get("confidence", 0.0),
            cooking_capability=ls.get("cooking_capability", "none"),
            financial_comfort=ls.get("financial_comfort", "moderate"),
            health_consciousness=ls.get("health_consciousness", "somewhat"),
            ordering_frequency=ls.get("ordering_frequency", 4.0),
            variety_seeking=ls.get("variety_seeking", 0.3),
        )

        # Habit Profile
        hp = data.get("habit_profile", {})
        dna.habit_profile = HabitProfile(
            overall_habit_strength=hp.get("overall_habit_strength", 0.5),
            reorder_speed=hp.get("reorder_speed", 120.0),
            restaurant_loyalty=hp.get("restaurant_loyalty", 0.5),
            item_loyalty=hp.get("item_loyalty", 0.5),
            recurring_items=hp.get("recurring_items", []),
            recurring_restaurants=hp.get("recurring_restaurants", []),
            temporal_habits=hp.get("temporal_habits", []),
            variety_seeking=hp.get("variety_seeking", 0.3),
            new_item_rate=hp.get("new_item_rate", 0.2),
            new_restaurant_rate=hp.get("new_restaurant_rate", 0.15),
        )

        return dna

    @classmethod
    def from_json(cls, filepath: str | Path) -> tuple["FoodDNA", dict[str, Any]]:
        """Load a Food DNA profile from a JSON file.

        Returns (dna, metadata) where metadata contains profile info
        like name, age, city, avatar, tagline, sample_conversations.
        """
        path = Path(filepath)
        with open(path) as f:
            data = json.load(f)

        # Extract metadata (not part of FoodDNA dataclass)
        metadata = {
            "id": data.get("id", ""),
            "name": data.get("name", ""),
            "age": data.get("age", 0),
            "city": data.get("city", ""),
            "origin": data.get("origin", ""),
            "avatar": data.get("avatar", ""),
            "tagline": data.get("tagline", ""),
            "sample_conversations": data.get("sample_conversations", []),
        }

        dna = cls.from_dict(data)
        return dna, metadata
