"""
Food DNA Agent — Nudge Engine

Determines when, what, and how to nudge users with food suggestions.
Implements psychological framing, suppression rules, and intensity levels.

Psychological frameworks used:
- Habit Loop (Duhigg): Cue → Routine → Reward
- Self-Determination Theory (Deci & Ryan): Autonomy, competence, relatedness
- Nudge Theory (Thaler & Sunstein): Choice architecture
- Transtheoretical Model (Prochaska): Stages of change
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .food_dna import ChangeStage, FoodDNA
from .recommender import Recommendation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Nudge intensity levels
# ---------------------------------------------------------------------------

class NudgeIntensity:
    """Nudge intensity levels — from subtle to direct.

    Suggestion: Subtle, dismissible, one option. Low confidence.
    Recommendation: 2-3 options with reasoning. Medium confidence.
    Reminder: Direct, action-oriented. High confidence + strong habit.
    """
    SUGGESTION = "suggestion"
    RECOMMENDATION = "recommendation"
    REMINDER = "reminder"


# ---------------------------------------------------------------------------
# Nudge record
# ---------------------------------------------------------------------------

@dataclass
class NudgeRecord:
    """Record of a nudge sent to the user."""

    timestamp: datetime
    nudge_type: str  # "habit", "time", "festival", "rain", "emotional"
    intensity: str
    content: str
    dismissed: bool = False


# ---------------------------------------------------------------------------
# Suppression rules
# ---------------------------------------------------------------------------

@dataclass
class SuppressionState:
    """Tracks nudge suppression for a user.

    Rules from the taxonomy:
    - Quiet hours: 11 PM – 8 AM (unless user has late-night pattern)
    - Stress detection: suppress health nudges, allow comfort nudges
    - Nudge fatigue: max 3 nudges per day
    - Rejection tracking: suppress same type for 4 hours after dismissal
    - Explicit stop: suppress all for 7 days
    """
    nudges_today: int = 0
    last_nudge_time: Optional[datetime] = None
    dismissed_types: dict[str, datetime] = field(default_factory=dict)
    explicit_stop_until: Optional[datetime] = None


def should_suppress(
    dna: FoodDNA,
    state: SuppressionState,
    nudge_type: str,
    current_hour: int,
) -> tuple[bool, str]:
    """Check if a nudge should be suppressed.

    Returns:
        (should_suppress, reason)
    """
    now = datetime.now()

    # Explicit stop
    if state.explicit_stop_until and now < state.explicit_stop_until:
        return True, "User requested no suggestions"

    # Quiet hours (23:00 – 08:00)
    # Exception: user has active late-night pattern (lr > 0.2)
    if current_hour >= 23 or current_hour < 8:
        if dna.temporal_pattern.late_night_ratio > 0.2:
            pass  # Allow — user is a late-night orderer
        else:
            return True, "Quiet hours"

    # Nudge fatigue (max 3 per day)
    if state.nudges_today >= 3:
        return True, "Nudge fatigue — max 3 per day"

    # Rejection tracking (suppress same type for 4 hours)
    if nudge_type in state.dismissed_types:
        dismissed_at = state.dismissed_types[nudge_type]
        if (now - dismissed_at).total_seconds() < 4 * 3600:
            return True, f"User dismissed {nudge_type} nudge recently"

    # Stress detection (suppress health nudges only)
    if dna.emotional_patterns.stress_level > 0.7:
        if nudge_type == "health":
            return True, "User is stressed — not a good time for health nudges"

    return False, ""


# ---------------------------------------------------------------------------
# Nudge framing (psychological frameworks)
# ---------------------------------------------------------------------------

FRAMING_TEMPLATES: dict[str, dict[str, str]] = {
    "habit_reinforcement": {
        NudgeIntensity.SUGGESTION: "By the way, it's {cue}…",
        NudgeIntensity.RECOMMENDATION: "{cue}! Your usual {routine}? Or want to try something new?",
        NudgeIntensity.REMINDER: "Your usual {routine} is ready to order. One tap to confirm.",
    },
    "variety_seeking": {
        NudgeIntensity.SUGGESTION: "Love {familiar}? You might enjoy {novel} — same comfort, different twist.",
        NudgeIntensity.RECOMMENDATION: "How about {novel}? You usually love {familiar}, and this is similar but fresh.",
        NudgeIntensity.REMINDER: "Time to shake things up! {novel} — trust me.",
    },
    "emotional_comfort": {
        NudgeIntensity.SUGGESTION: "Tough day? Here's something warm. ☕",
        NudgeIntensity.RECOMMENDATION: "Tough day? Your comfort {food} from {restaurant}. No judgment.",
        NudgeIntensity.REMINDER: "Your comfort {food} — because you deserve it today.",
    },
    "health_nudge": {
        NudgeIntensity.SUGGESTION: "Light and fresh option available — {food}.",
        NudgeIntensity.RECOMMENDATION: "Feeling health-conscious? {food} — packed with goodness, still delicious.",
        NudgeIntensity.REMINDER: "Your healthy streak continues! {food} today?",
    },
    "festival": {
        NudgeIntensity.SUGGESTION: "It's {festival}! 🪔",
        NudgeIntensity.RECOMMENDATION: "{festival} vibes! 🪔 How about traditional {food}?",
        NudgeIntensity.REMINDER: "{festival} tomorrow! Order your {food} now for the celebration.",
    },
    "price_sensitive": {
        NudgeIntensity.SUGGESTION: "Great deal available — {food}.",
        NudgeIntensity.RECOMMENDATION: "₹{price} {food} — {discount}% off! You save ₹{savings}.",
        NudgeIntensity.REMINDER: "Your usual {food} at ₹{price} — {discount}% off today only!",
    },
    "social_context": {
        NudgeIntensity.SUGGESTION: "Family dinner tonight?",
        NudgeIntensity.RECOMMENDATION: "Family dinner? Combo for {size} at ₹{price} — something for everyone.",
        NudgeIntensity.REMINDER: "Your usual family combo — {size} people, ₹{price}. Order now?",
    },
    "decision_fatigue": {
        NudgeIntensity.SUGGESTION: "Quick option: {food}.",
        NudgeIntensity.RECOMMENDATION: "Don't overthink it — {food} from {restaurant}. Yes or no?",
        NudgeIntensity.REMINDER: "Yes or no: {food} from {restaurant}.",
    },
}


def select_intensity(dna: FoodDNA, nudge_type: str) -> str:
    """Select nudge intensity based on confidence and context.

    Low confidence → suggestion (subtle)
    High habit strength → reminder (direct)
    Default → recommendation (moderate)
    """
    if dna.confidence_score < 0.3:
        return NudgeIntensity.SUGGESTION
    if nudge_type == "habit" and dna.habit_profile.overall_habit_strength > 0.7:
        return NudgeIntensity.REMINDER
    if dna.emotional_patterns.stress_level > 0.6:
        return NudgeIntensity.SUGGESTION  # Don't add cognitive load when stressed
    return NudgeIntensity.RECOMMENDATION


def format_nudge(
    template_key: str,
    intensity: str,
    **kwargs: Any,
) -> str:
    """Format a nudge message using psychological framing templates."""
    templates = FRAMING_TEMPLATES.get(template_key, {})
    template = templates.get(intensity, templates.get(NudgeIntensity.RECOMMENDATION, "{food}"))
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


# ---------------------------------------------------------------------------
# Nudge engine
# ---------------------------------------------------------------------------

class NudgeEngine:
    """Decides when, what, and how to nudge users.

    The nudge engine sits between the recommendation engine and the user,
    applying psychological rules to determine:
    1. WHEN to nudge (timing rules, suppression checks)
    2. WHAT to nudge (Food DNA-weighted selection)
    3. HOW to nudge (framing per psychological framework)
    """

    def __init__(self, dna: FoodDNA, suppression_state: Optional[SuppressionState] = None) -> None:
        self.dna = dna
        self.state = suppression_state or SuppressionState()

    def should_nudge(self, nudge_type: str, current_hour: int) -> tuple[bool, str]:
        """Check if we should send a nudge right now."""
        return should_suppress(self.dna, self.state, nudge_type, current_hour)

    def record_nudge(self, nudge_type: str, intensity: str, content: str) -> None:
        """Record that a nudge was sent."""
        self.state.nudges_today += 1
        self.state.last_nudge_time = datetime.now()

    def record_dismissal(self, nudge_type: str) -> None:
        """Record that the user dismissed a nudge."""
        self.state.dismissed_types[nudge_type] = datetime.now()

    def record_explicit_stop(self, days: int = 7) -> None:
        """Record that the user explicitly asked to stop nudges."""
        from datetime import timedelta
        self.state.explicit_stop_until = datetime.now() + timedelta(days=days)

    def build_habit_nudge(self, habit: dict[str, Any], current_hour: int) -> Optional[str]:
        """Build a habit-reinforcement nudge.

        Habit loop: Cue (time/day) → Routine (what they order) → Reward (why)
        The agent reinforces the habit by acknowledging the cue and offering the routine.
        """
        nudge_type = "habit"
        suppressed, reason = self.should_nudge(nudge_type, current_hour)
        if suppressed:
            logger.debug("Habit nudge suppressed: %s", reason)
            return None

        intensity = select_intensity(self.dna, nudge_type)
        cue = habit.get("cue", "")
        routine = habit.get("item", habit.get("name", "your usual"))

        content = format_nudge(
            "habit_reinforcement",
            intensity,
            cue=cue.title() if cue else "This time",
            routine=routine,
        )

        self.record_nudge(nudge_type, intensity, content)
        return content

    def build_festival_nudge(self, festival_name: str, festival_foods: list[str], current_hour: int) -> Optional[str]:
        """Build a festival-aware nudge.

        Indian festivals have strong food associations — the agent leverages
        cultural psychology to suggest timely, identity-affirming food.
        """
        nudge_type = "festival"
        suppressed, reason = self.should_nudge(nudge_type, current_hour)
        if suppressed:
            return None

        intensity = select_intensity(self.dna, nudge_type)
        # Filter foods by dietary identity
        safe_foods = []
        for food in festival_foods:
            item_check = {"name": food}
            from .recommender import satisfies_dietary
            if satisfies_dietary(item_check, self.dna.dietary_identity):
                safe_foods.append(food)

        if not safe_foods:
            return None

        content = format_nudge(
            "festival",
            intensity,
            festival=festival_name.title(),
            food=safe_foods[0].replace("_", " "),
        )

        self.record_nudge(nudge_type, intensity, content)
        return content

    def build_emotional_nudge(self, food: str, restaurant: str, current_hour: int) -> Optional[str]:
        """Build an emotional comfort nudge.

        Key: NEVER push health food on a stressed user.
        Serve the emotional need first, not long-term goals.
        """
        nudge_type = "emotional"
        suppressed, reason = self.should_nudge(nudge_type, current_hour)
        if suppressed:
            return None

        intensity = select_intensity(self.dna, nudge_type)

        content = format_nudge(
            "emotional_comfort",
            intensity,
            food=food,
            restaurant=restaurant,
        )

        self.record_nudge(nudge_type, intensity, content)
        return content

    def build_decision_fatigue_nudge(self, food: str, restaurant: str, current_hour: int) -> Optional[str]:
        """Build a decision-fatigue nudge (minimize choices).

        At 10 PM after a weekday, users don't want to browse.
        Give them one yes/no option.
        """
        nudge_type = "decision_fatigue"
        suppressed, reason = self.should_nudge(nudge_type, current_hour)
        if suppressed:
            return None

        intensity = NudgeIntensity.REMINDER  # Decision fatigue → be direct

        content = format_nudge(
            "decision_fatigue",
            intensity,
            food=food,
            restaurant=restaurant,
        )

        self.record_nudge(nudge_type, intensity, content)
        return content

    def build_price_nudge(self, food: str, price: float, discount_pct: float, current_hour: int) -> Optional[str]:
        """Build a price-sensitive nudge with anchoring and loss aversion framing.

        Psychological basis: Behavioral economics.
        "You saved ₹X" (endowment effect) is more motivating than "Get ₹X off".
        Always show original price + discount together (anchoring).
        """
        nudge_type = "price"
        suppressed, reason = self.should_nudge(nudge_type, current_hour)
        if suppressed:
            return None

        intensity = select_intensity(self.dna, nudge_type)
        savings = price * discount_pct / 100

        content = format_nudge(
            "price_sensitive",
            intensity,
            food=food,
            price=int(price),
            discount=int(discount_pct),
            savings=int(savings),
        )

        self.record_nudge(nudge_type, intensity, content)
        return content
