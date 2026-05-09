"""
Food DNA Agent — Recommendation Engine

Generates personalized food recommendations from the Food DNA profile.
Supports proactive (agent-initiated) and reactive (user-initiated) modes.
Implements scoring, dietary hard filters, and voice/chat response shaping.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .food_dna import (
    ChangeStage,
    DietaryType,
    FoodDNA,
    LifeStageType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Festival calendar (Indian festivals with food associations)
# ---------------------------------------------------------------------------

FESTIVAL_CALENDAR: dict[str, dict[str, Any]] = {
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


# ---------------------------------------------------------------------------
# Recommendation candidate
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """A scored food recommendation candidate."""

    name: str
    restaurant: str = ""
    cuisine: str = ""
    price: float = 0.0
    delivery_time: str = ""
    score: float = 0.0
    source: str = ""  # "habit", "proactive", "reactive", "cross_server"
    reasoning: str = ""
    short_description: str = ""
    long_description: str = ""

    def to_voice_string(self, index: int = 0) -> str:
        """Format for voice output (≤3 options, spoken prices)."""
        price_spoken = f"{int(self.price)} rupees" if self.price else ""
        parts = []
        if index > 0:
            parts.append(f"{index}.")
        parts.append(self.name)
        if self.restaurant:
            parts.append(f"from {self.restaurant}")
        if price_spoken:
            parts.append(price_spoken)
        if self.delivery_time:
            parts.append(self.delivery_time)
        return " ".join(parts)

    def to_chat_string(self, index: int = 0) -> str:
        """Format for chat output (rich markdown)."""
        lines = [f"**{index}. {self.name}**"]
        if self.restaurant:
            lines[0] += f" — {self.restaurant}"
        if self.short_description:
            lines.append(f"   {self.short_description}")
        price_str = f"💰 ₹{int(self.price)}" if self.price else ""
        time_str = f"🕐 {self.delivery_time}" if self.delivery_time else ""
        meta = " · ".join(filter(None, [price_str, time_str]))
        if meta:
            lines.append(f"   {meta}")
        if self.reasoning:
            lines.append(f"   _{self.reasoning}_")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def satisfies_dietary(item: dict[str, Any], dietary: FoodDNA.dietary_identity.__class__) -> bool:
    """Hard filter: does this item satisfy the user's dietary identity?

    This is a BINARY gate — 0 or 1. A vegetarian user NEVER gets non-veg suggestions.
    Psychological basis: Self-affirmation theory. Dietary identity is not a preference.
    """
    item_name = (item.get("name", "") or item.get("itemName", "")).lower()
    item_cuisine = item.get("cuisine", "").lower()

    non_veg_keywords = {"chicken", "mutton", "fish", "prawn", "beef", "pork", "lamb", "meat", "egg"}

    if dietary.primary == DietaryType.VEGETARIAN:
        return not any(kw in item_name for kw in non_veg_keywords)

    if dietary.primary == DietaryType.EGGETARIAN:
        meat_keywords = {"chicken", "mutton", "fish", "prawn", "beef", "pork", "lamb", "meat"}
        return not any(kw in item_name for kw in meat_keywords)

    if dietary.primary == DietaryType.JAIN:
        jain_forbidden = {"onion", "garlic", "potato", "carrot", "beetroot", "radish", "turnip", "egg"}
        if any(kw in item_name for kw in jain_forbidden):
            return False
        return satisfies_dietary(item, dietary)  # Also check vegetarian

    if dietary.primary == DietaryType.VEGAN:
        animal_keywords = {"chicken", "mutton", "fish", "prawn", "beef", "pork", "lamb", "meat",
                           "egg", "milk", "cheese", "butter", "ghee", "cream", "paneer", "curd", "yogurt"}
        return not any(kw in item_name for kw in animal_keywords)

    return True  # Non-vegetarian: anything goes


def score_candidate(item: dict[str, Any], dna: FoodDNA, context: dict[str, Any]) -> float:
    """Score a food item for recommendation given user's Food DNA and context.

    Weights from the taxonomy:
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
    """
    # Hard filter
    if not satisfies_dietary(item, dna.dietary_identity):
        return 0.0

    score = 0.0
    cuisine = item.get("cuisine", "other")

    # Regional affinity (0.20)
    regional_score = dna.regional_identity.cuisine_affinity.get(cuisine, 0.1)
    score += regional_score * 0.20

    # Temporal fit (0.15) — is this appropriate for current meal?
    hour = context.get("hour", 12)
    if 6 <= hour <= 10:  # Breakfast
        breakfast_cuisines = {"south_indian", "healthy"}
        temporal_score = 0.8 if cuisine in breakfast_cuisines else 0.4
    elif 12 <= hour <= 15:  # Lunch
        temporal_score = 0.7
    elif 18 <= hour <= 22:  # Dinner
        temporal_score = 0.8
    else:  # Late night / odd hours
        comfort_cuisines = {"street_food", "chinese", "fast_food"}
        temporal_score = 0.7 if cuisine in comfort_cuisines else 0.3
    score += temporal_score * 0.15

    # Habit reinforcement (0.15)
    habit_score = 0.0
    item_name = item.get("name", "").lower()
    for habit_item in dna.habit_profile.recurring_items:
        if habit_item.get("item", "").lower() in item_name or item_name in habit_item.get("item", "").lower():
            habit_score = habit_item.get("strength", 0.5)
            break
    for habit_rest in dna.habit_profile.recurring_restaurants:
        if habit_rest.get("name", "").lower() in item.get("restaurant", "").lower():
            habit_score = max(habit_score, habit_rest.get("strength", 0.5) * 0.8)
            break
    score += habit_score * 0.15

    # Price fit (0.10)
    price = item.get("price", 0)
    if price > 0 and dna.price_psychology.avg_order_value > 0:
        price_ratio = price / dna.price_psychology.avg_order_value
        if 0.5 <= price_ratio <= 1.5:
            price_score = 1.0
        elif price_ratio < 0.5:
            price_score = 0.6  # Too cheap — might feel low quality
        else:
            price_score = max(0.2, 1.0 - (price_ratio - 1.5))  # Too expensive
        score += price_score * 0.10

    # Emotional fit (0.10) — comfort food when stressed
    emotional_score = 0.5  # neutral
    if dna.emotional_patterns.stress_level > 0.6:
        if item_name in [f.lower() for f in dna.emotional_patterns.comfort_foods]:
            emotional_score = 1.0
    elif dna.emotional_patterns.celebration_level > 0.6:
        if item_name in [f.lower() for f in dna.emotional_patterns.celebration_foods]:
            emotional_score = 1.0
    score += emotional_score * 0.10

    # Social fit (0.05)
    social_score = 0.5
    party_size = context.get("party_size", 1)
    if party_size >= 3 and dna.social_dynamics.family_ratio > 0.3:
        social_score = 0.8  # Family-appropriate
    elif party_size == 1 and dna.social_dynamics.solo_ratio > 0.5:
        social_score = 0.7  # Solo-appropriate
    score += social_score * 0.05

    # Health alignment (0.05)
    health_score = 0.5
    if dna.health_orientation.change_stage in (ChangeStage.ACTION, ChangeStage.MAINTENANCE):
        # User is actively health-conscious
        healthy_keywords = {"salad", "grilled", "steamed", "protein", "quinoa", "oats"}
        if any(kw in item_name for kw in healthy_keywords):
            health_score = 0.9
    score += health_score * 0.05

    # Variety bonus (0.05)
    variety_score = dna.habit_profile.variety_seeking * 0.5  # Moderate bonus for variety
    score += variety_score * 0.05

    return round(score, 4)


# ---------------------------------------------------------------------------
# Response shaper
# ---------------------------------------------------------------------------

def shape_response(
    recommendations: list[Recommendation],
    channel: str = "chat",
    greeting: str = "",
) -> str:
    """Shape recommendations for voice or chat output.

    Voice: ≤3 options, spoken prices, 1-2 sentences per option.
    Chat: ≤8 options, rich markdown, full details.
    """
    if channel == "voice":
        return _shape_voice(recommendations, greeting)
    return _shape_chat(recommendations, greeting)


def _shape_voice(recommendations: list[Recommendation], greeting: str) -> str:
    """Voice response: concise, natural, confirmatory."""
    top = recommendations[:3]
    if not top:
        return "I couldn't find anything matching your preferences right now. Want me to try something different?"

    parts = []
    if greeting:
        parts.append(greeting)

    if len(top) == 1:
        r = top[0]
        parts.append(f"How about {r.to_voice_string()}? Want me to order that?")
    else:
        parts.append("Here are your top picks:")
        for i, r in enumerate(top, 1):
            parts.append(r.to_voice_string(i))
        parts.append("Which one?")

    return " ".join(parts)


def _shape_chat(recommendations: list[Recommendation], greeting: str) -> str:
    """Chat response: rich markdown with details."""
    top = recommendations[:8]
    if not top:
        return "I couldn't find anything matching your preferences right now. Want me to try something different?"

    parts = []
    if greeting:
        parts.append(greeting)
    else:
        parts.append("🍽️ **Your personalized picks:**")

    for i, r in enumerate(top, 1):
        parts.append(r.to_chat_string(i))

    parts.append("\nTap a restaurant to view menu, or say the number to order!")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Recommendation engines
# ---------------------------------------------------------------------------

class Recommender:
    """Generates recommendations from Food DNA profiles.

    Three modes:
    1. Proactive: agent-initiated (time-based, pattern-based, festival)
    2. Reactive: user-initiated ("order something", "surprise me")
    3. Cross-server: combining Food + Instamart + Dineout signals
    """

    def __init__(self, dna: FoodDNA) -> None:
        self.dna = dna

    # -- proactive -----------------------------------------------------------

    def proactive_time_based(self, current_hour: int) -> Optional[Recommendation]:
        """Suggest food based on user's typical meal ordering window.

        If current hour ± 30 min matches a high-density ordering window,
        generate a time-based nudge.
        """
        hour_dist = self.dna.temporal_pattern.hour_distribution
        if not hour_dist or sum(hour_dist) == 0:
            return None

        # Check current hour and neighbors
        density = hour_dist[current_hour]
        if current_hour > 0:
            density += hour_dist[current_hour - 1] * 0.5
        if current_hour < 23:
            density += hour_dist[current_hour + 1] * 0.5

        if density < 0.1:  # Not a typical ordering time
            return None

        # Find the top cuisine for this time of day
        top_cuisines = sorted(
            self.dna.cuisine_preferences.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        if not top_cuisines:
            return None

        top_cuisine = top_cuisines[0][0]

        # Build recommendation
        meal = "breakfast" if 6 <= current_hour <= 10 else "lunch" if 11 <= current_hour <= 15 else "dinner"
        return Recommendation(
            name=f"Your usual {meal}",
            cuisine=top_cuisine,
            source="proactive_time",
            reasoning=f"Your typical {meal} ordering time",
            short_description=f"Time for {meal}!",
        )

    def proactive_friday_biryani(self, day_of_week: int, hour: int) -> Optional[Recommendation]:
        """Detect Friday biryani habit — a culturally reinforced pattern.

        Psychological basis: Habit loop theory. Friday evening → biryani →
        weekend celebration reward. This is one of the strongest food habits
        in Indian food culture.
        """
        if day_of_week != 4:  # Friday = 4 (Monday=0)
            return None

        # Check for Friday dinner pattern
        day_dist = self.dna.temporal_pattern.day_distribution
        if not day_dist or day_dist[4] < 0.15:  # Not a heavy Friday orderer
            return None

        # Check if it's evening (typical biryani time)
        if hour < 17:
            return None

        # Check for biryani in top items or cuisine preferences
        north_indian = self.dna.cuisine_preferences.get("north_indian", 0)
        has_biryani = any(
            "biryani" in h.get("item", "").lower()
            for h in self.dna.habit_profile.recurring_items
        )

        if has_biryani or north_indian > 0.2:
            return Recommendation(
                name="Biryani",
                cuisine="north_indian",
                source="proactive_friday",
                reasoning="Your Friday celebration tradition",
                short_description="Friday vibes! 🎉",
            )

        return None

    def proactive_festival(self, festival_name: str) -> Optional[Recommendation]:
        """Suggest festival-appropriate food.

        Indian festivals have specific food associations — the agent
        leverages cultural psychology to suggest timely, identity-affirming food.
        """
        festival = FESTIVAL_CALENDAR.get(festival_name.lower())
        if not festival:
            return None

        foods = festival["foods"]
        # Filter by dietary identity
        dietary = self.dna.dietary_identity
        safe_foods = []
        for food in foods:
            if dietary.primary == DietaryType.VEGETARIAN:
                meat_keywords = {"chicken", "mutton", "fish", "beef", "pork", "meat"}
                if not any(kw in food for kw in meat_keywords):
                    safe_foods.append(food)
            else:
                safe_foods.append(food)

        if not safe_foods:
            return None

        return Recommendation(
            name=safe_foods[0].replace("_", " ").title(),
            cuisine="dessert" if "sweet" in foods[0] or "mithai" in foods[0] else "street_food",
            source="proactive_festival",
            reasoning=f"{festival_name.title()} special!",
            short_description=f"🪔 {festival_name.title()} vibes!",
        )

    def proactive_rain(self, is_raining: bool) -> Optional[Recommendation]:
        """Suggest comfort food when it's raining.

        Rain → hot fried snacks is a universal Indian trigger.
        Psychological basis: Environmental cue → comfort food activation.
        """
        if not is_raining:
            return None

        comfort = self.dna.emotional_patterns.comfort_foods
        if comfort:
            return Recommendation(
                name=comfort[0],
                source="proactive_rain",
                reasoning="Perfect weather for comfort food",
                short_description="🌧️ Rainy day comfort!",
            )

        # Default rain food
        return Recommendation(
            name="Hot Pakora",
            cuisine="street_food",
            source="proactive_rain",
            reasoning="Classic rainy day snack",
            short_description="🌧️ Rainy day comfort!",
        )

    # -- reactive ------------------------------------------------------------

    def reactive_order_something(self, context: dict[str, Any]) -> list[Recommendation]:
        """Handle 'order something' — general recommendation.

        Uses Food DNA to rank available options.
        """
        candidates = self._get_default_candidates(context)
        scored = []
        for item in candidates:
            s = score_candidate(item, self.dna, context)
            if s > 0:
                scored.append(Recommendation(
                    name=item.get("name", ""),
                    restaurant=item.get("restaurant", ""),
                    cuisine=item.get("cuisine", ""),
                    price=item.get("price", 0),
                    delivery_time=item.get("delivery_time", ""),
                    score=s,
                    source="reactive_general",
                    reasoning=self._explain_score(item, s),
                    short_description=item.get("short_description", ""),
                ))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored

    def reactive_something_healthy(self, context: dict[str, Any]) -> list[Recommendation]:
        """Handle 'something healthy' — health-filtered recommendations.

        Respects the user's stage of change:
        - Pre-contemplation → shouldn't happen (user initiated)
        - Contemplation → gentle framing: "light and fresh" not "diet food"
        - Action/Maintenance → specific health metrics
        """
        candidates = self._get_default_candidates(context)

        # Health filter
        healthy_keywords = {"salad", "grilled", "steamed", "protein", "quinoa", "oats", "soup", "light"}
        filtered = []
        for item in candidates:
            name_lower = item.get("name", "").lower()
            if any(kw in name_lower for kw in healthy_keywords):
                filtered.append(item)
            elif item.get("cuisine") == "healthy":
                filtered.append(item)

        # If no healthy options found, fall back to all candidates but boost health score
        if not filtered:
            filtered = candidates

        scored = []
        for item in filtered:
            # Boost health score for this query
            s = score_candidate(item, self.dna, context)
            # Extra health boost
            name_lower = item.get("name", "").lower()
            if any(kw in name_lower for kw in healthy_keywords):
                s += 0.15
            if s > 0:
                # Use positive framing based on change stage
                if self.dna.health_orientation.change_stage in (ChangeStage.CONTEMPLATION, ChangeStage.PREPARATION):
                    reasoning = "Fresh and light option"
                else:
                    reasoning = "Healthy choice that matches your taste"
                scored.append(Recommendation(
                    name=item.get("name", ""),
                    restaurant=item.get("restaurant", ""),
                    cuisine=item.get("cuisine", ""),
                    price=item.get("price", 0),
                    delivery_time=item.get("delivery_time", ""),
                    score=s,
                    source="reactive_healthy",
                    reasoning=reasoning,
                    short_description=item.get("short_description", ""),
                ))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored

    def reactive_surprise_me(self, context: dict[str, Any]) -> list[Recommendation]:
        """Handle 'surprise me' — controlled novelty.

        Selects items in the "surprise zone": score between 0.4-0.7
        (familiar-but-different). One wild card included.

        Psychological basis: Sensory-specific satiety, variety-seeking behavior.
        User wants surprise, not risk.
        """
        candidates = self._get_default_candidates(context)
        scored = []
        for item in candidates:
            s = score_candidate(item, self.dna, context)
            scored.append((item, s))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Surprise zone: not top picks, not random
        surprise = []
        for item, s in scored:
            if 0.3 <= s <= 0.7:
                surprise.append(Recommendation(
                    name=item.get("name", ""),
                    restaurant=item.get("restaurant", ""),
                    cuisine=item.get("cuisine", ""),
                    price=item.get("price", 0),
                    delivery_time=item.get("delivery_time", ""),
                    score=s,
                    source="reactive_surprise",
                    reasoning=f"Trust me on this one — {item.get('name', '')}",
                    short_description="Something different!",
                ))

        # Add one wild card (novelty)
        if scored:
            wild = scored[-1]  # Lowest score = most novel
            surprise.append(Recommendation(
                name=wild[0].get("name", ""),
                restaurant=wild[0].get("restaurant", ""),
                cuisine=wild[0].get("cuisine", ""),
                price=wild[0].get("price", 0),
                score=wild[1],
                source="reactive_surprise_wild",
                reasoning="A wild card — live a little!",
                short_description="Wild card! 🎲",
            ))

        return surprise

    # -- cross-server --------------------------------------------------------

    def cross_server_restaurant_closed(
        self,
        closed_restaurant: str,
        available_restaurants: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[Recommendation]:
        """Handle restaurant closure — suggest similar alternatives.

        Cross-references Food DNA to find restaurants with similar cuisine
        profile and comparable price range.
        """
        # Find the cuisine of the closed restaurant
        closed_cuisine = "other"
        for rest in self.dna.habit_profile.recurring_restaurants:
            if rest.get("name", "").lower() == closed_restaurant.lower():
                closed_cuisine = rest.get("cuisine", "other")
                break

        scored = []
        for item in available_restaurants:
            s = score_candidate(item, self.dna, context)
            # Boost same-cuisine alternatives
            if item.get("cuisine") == closed_cuisine:
                s += 0.2
            if s > 0:
                scored.append(Recommendation(
                    name=item.get("name", ""),
                    restaurant=item.get("restaurant", ""),
                    cuisine=item.get("cuisine", ""),
                    price=item.get("price", 0),
                    delivery_time=item.get("delivery_time", ""),
                    score=s,
                    source="cross_server_alternative",
                    reasoning=f"Similar to {closed_restaurant}",
                    short_description=f"Like {closed_restaurant} but different",
                ))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored

    # -- helpers -------------------------------------------------------------

    def _get_default_candidates(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Get default candidate items based on Food DNA.

        In production, this would call MCP search_restaurants.
        For the MVP, we generate candidates from the profile.
        """
        candidates = []
        top_cuisines = sorted(
            self.dna.cuisine_preferences.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for cuisine, affinity in top_cuisines[:5]:
            if affinity < 0.05:
                continue
            candidates.append({
                "name": f"{cuisine.replace('_', ' ').title()} Special",
                "restaurant": "",
                "cuisine": cuisine,
                "price": self.dna.price_psychology.avg_order_value or 250,
                "delivery_time": "30-40 min",
                "short_description": f"Your favorite {cuisine.replace('_', ' ')}",
            })

        # Add recurring items
        for habit in self.dna.habit_profile.recurring_items[:3]:
            candidates.append({
                "name": habit.get("item", ""),
                "restaurant": "",
                "cuisine": "other",
                "price": self.dna.price_psychology.avg_order_value or 250,
                "delivery_time": "30-40 min",
                "short_description": "Your usual",
            })

        return candidates

    def _explain_score(self, item: dict[str, Any], score: float) -> str:
        """Generate a human-readable explanation for why this item was recommended."""
        reasons = []
        cuisine = item.get("cuisine", "other")

        # Check habit match
        item_name = item.get("name", "").lower()
        for h in self.dna.habit_profile.recurring_items:
            if h.get("item", "").lower() in item_name:
                reasons.append("your usual")
                break

        # Check cuisine affinity
        affinity = self.dna.cuisine_preferences.get(cuisine, 0)
        if affinity > 0.3:
            reasons.append(f"you love {cuisine.replace('_', ' ')}")

        if not reasons:
            reasons.append("matches your taste")

        return "Based on " + ", ".join(reasons)
