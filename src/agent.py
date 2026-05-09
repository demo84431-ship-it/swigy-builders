"""
Food DNA Agent — Main Agent Orchestrator

Central coordinator that connects to Swiggy's 3 MCP servers, extracts
behavioral signals, builds Food DNA profiles, and generates personalized
recommendations. Handles the 5 demo scenarios.

Architecture:
    User Intent → MCP Calls → Feature Extraction → Food DNA Update → Recommendation → Response
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .config import Config
from .feature_extractor import (
    extract_all_features,
    extract_from_food_orders,
    extract_from_go_to_items,
    extract_from_booking_status,
    extract_from_addresses,
    extract_from_search_restaurants,
)
from .food_dna import FoodDNA
from .food_dna_calculator import FoodDNACalculator
from .mcp_client import MCPClient, MCPError, ErrorBucket
from .nudge_engine import NudgeEngine, SuppressionState
from .recommender import (
    FESTIVAL_CALENDAR,
    Recommender,
    Recommendation,
    shape_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent context (per-session state)
# ---------------------------------------------------------------------------

@dataclass
class AgentContext:
    """Per-session context for the agent.

    Tracks the current interaction state — addresses, channel type,
    recent MCP responses, and conversation history.
    """
    channel: str = "chat"  # "voice" or "chat"
    current_address_id: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    current_hour: int = 12
    day_of_week: int = 0  # Monday=0
    is_raining: bool = False
    festival_name: Optional[str] = None
    party_size: int = 1

    # Cached MCP responses
    addresses: list[dict[str, Any]] = field(default_factory=list)
    last_search_results: list[dict[str, Any]] = field(default_factory=list)

    # Conversation state
    pending_confirmation: Optional[dict[str, Any]] = None
    last_tool_call: Optional[str] = None


# ---------------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------------

class FoodDNAAgent:
    """The Food DNA Agent — learns Indian users' food behavior patterns
    from Swiggy MCP signals and generates personalized recommendations.

    Usage:
        async with FoodDNAAgent(config) as agent:
            # Authenticate
            url, verifier, state = agent.get_auth_url()
            # ... user completes OAuth in browser ...
            await agent.authenticate(auth_code, verifier)

            # Build profile
            await agent.build_profile()

            # Get recommendations
            response = await agent.handle_intent("order something")
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()
        self._mcp: Optional[MCPClient] = None
        self._calculator = FoodDNACalculator()

        # User state
        self.dna: Optional[FoodDNA] = None
        self.context = AgentContext()
        self._nudge_state = SuppressionState()

    async def __aenter__(self) -> "FoodDNAAgent":
        self._mcp = MCPClient(self._config)
        await self._mcp.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._mcp:
            await self._mcp.__aexit__(*exc)

    # -- authentication ------------------------------------------------------

    def get_auth_url(self) -> tuple[str, str, str]:
        """Generate OAuth authorization URL.

        Returns:
            (authorize_url, code_verifier, state) — store verifier+state for callback.
        """
        assert self._mcp is not None
        return self._mcp.get_auth_url()

    async def authenticate(self, auth_code: str, code_verifier: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        assert self._mcp is not None
        return await self._mcp.authenticate(auth_code, code_verifier)

    # -- profile building ----------------------------------------------------

    async def build_profile(self, user_id: str = "default") -> FoodDNA:
        """Build or update the Food DNA profile by fetching signals from all 3 MCP servers.

        This is the core pipeline:
        1. Fetch signals from Food, Instamart, and Dineout servers
        2. Extract behavioral features from each response
        3. Build/update the Food DNA profile
        """
        assert self._mcp is not None
        mcp_responses: dict[str, dict[str, Any]] = {}

        # Fetch from all 3 servers in parallel-like fashion
        # Food server
        try:
            orders_resp = await self._mcp.food("get_food_orders")
            mcp_responses["get_food_orders"] = orders_resp
        except MCPError as e:
            logger.warning("Failed to fetch food orders: %s", e)

        try:
            addresses_resp = await self._mcp.food("get_addresses")
            mcp_responses["get_addresses"] = addresses_resp
            self.context.addresses = addresses_resp.get("addresses", [])
            if self.context.addresses:
                self.context.current_address_id = self.context.addresses[0].get("addressId")
        except MCPError as e:
            logger.warning("Failed to fetch addresses: %s", e)

        # Instamart server
        try:
            go_to_resp = await self._mcp.instamart("your_go_to_items")
            mcp_responses["your_go_to_items"] = go_to_resp
        except MCPError as e:
            logger.warning("Failed to fetch go-to items: %s", e)

        # Dineout server
        try:
            bookings_resp = await self._mcp.dineout("get_booking_status")
            mcp_responses["get_booking_status"] = bookings_resp
        except MCPError as e:
            logger.warning("Failed to fetch booking status: %s", e)

        # Extract features and build profile
        features = extract_all_features(mcp_responses)

        if self.dna is None:
            self.dna = self._calculator.build_from_features(features, user_id)
        else:
            self.dna = self._calculator.update(self.dna, features)

        logger.info(
            "Food DNA updated: %d data points, confidence %.2f",
            self.dna.data_points,
            self.dna.confidence_score,
        )

        return self.dna

    # -- intent handling -----------------------------------------------------

    async def handle_intent(
        self,
        intent: str,
        channel: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Handle a user intent and return a formatted response.

        Supported intents:
        - "order something" / "order my usual" → reactive recommendation
        - "something healthy" → health-filtered recommendation
        - "surprise me" → controlled novelty
        - "it's friday" → proactive Friday biryani
        - "plan my evening" → cross-server (Dineout + Food)
        - "diwali tomorrow" → festival-aware suggestion
        - Proactive nudges (called by scheduler, not user)
        """
        if channel:
            self.context.channel = channel

        intent_lower = intent.lower().strip()

        # Route to specific handlers
        if any(phrase in intent_lower for phrase in ["order my usual", "order something", "i want food"]):
            return await self._handle_order_something()
        if any(phrase in intent_lower for phrase in ["something healthy", "eat healthy", "healthy"]):
            return await self._handle_something_healthy()
        if any(phrase in intent_lower for phrase in ["surprise me", "something different", "bored"]):
            return await self._handle_surprise_me()
        if "friday" in intent_lower:
            return await self._handle_friday()
        if any(phrase in intent_lower for phrase in ["plan my evening", "plan evening", "dinner out"]):
            return await self._handle_plan_evening()
        if any(phrase in intent_lower for phrase in ["diwali", "holi", "festival", "eid", "christmas"]):
            return await self._handle_festival(intent_lower)
        if any(phrase in intent_lower for phrase in ["restaurant closed", "closed", "unavailable"]):
            return await self._handle_restaurant_closed(kwargs.get("restaurant_name", ""))

        # Default: general recommendation
        return await self._handle_order_something()

    # -- scenario handlers ---------------------------------------------------

    async def _handle_order_something(self) -> str:
        """Scenario 1: 'Order my usual' — behavioral lookup → confirm → order.

        Flow:
        1. Check Food DNA for habitual items/restaurants
        2. If high habit strength → suggest "your usual"
        3. If low habit strength → show top 3-8 options
        4. Voice: 3 options max. Chat: 8 options max.
        """
        assert self.dna is not None, "Build profile first"

        # Check if we have high habit strength — suggest "the usual"
        if self.dna.habit_profile.overall_habit_strength > 0.6:
            top_items = self.dna.habit_profile.recurring_items
            top_restaurants = self.dna.habit_profile.recurring_restaurants

            if top_items:
                item = top_items[0].get("item", "")
                restaurant = top_restaurants[0].get("name", "") if top_restaurants else ""

                if self.context.channel == "voice":
                    return f"Your usual {item} from {restaurant}? Want me to order that?"
                else:
                    return (
                        f"🍽️ **Your usual**\n\n"
                        f"**{item}** from **{restaurant}**\n"
                        f"Based on your ordering pattern — you love this!\n\n"
                        f"Shall I add it to your cart?"
                    )

        # Lower habit strength — show options
        recommender = Recommender(self.dna)
        context = self._build_context()
        recommendations = recommender.reactive_order_something(context)

        if not recommendations:
            return "I'm still learning your preferences. What are you in the mood for?"

        return shape_response(recommendations, self.context.channel, greeting=self._get_greeting())

    async def _handle_something_healthy(self) -> str:
        """Handle 'something healthy' — health-filtered recommendations.

        Respects the user's stage of change (Transtheoretical Model):
        - Pre-contemplation → gentle framing
        - Contemplation → "light and fresh" not "diet food"
        - Action → specific health metrics
        """
        assert self.dna is not None
        recommender = Recommender(self.dna)
        context = self._build_context()
        recommendations = recommender.reactive_something_healthy(context)

        if not recommendations:
            return "I don't have enough healthy options in your area right now. Want me to search for something specific?"

        # Use positive framing based on change stage
        if self.dna.health_orientation.change_stage in (ChangeStage.CONTEMPLATION, ChangeStage.PREPARATION):
            greeting = "🥗 Here are some light and fresh options:"
        else:
            greeting = "🥗 Healthy picks for you:"
        return shape_response(recommendations, self.context.channel, greeting=greeting)

    async def _handle_surprise_me(self) -> str:
        """Handle 'surprise me' — controlled novelty.

        Selects items in the "surprise zone" (familiar-but-different).
        Psychological basis: Sensory-specific satiety, variety-seeking behavior.
        """
        assert self.dna is not None
        recommender = Recommender(self.dna)
        context = self._build_context()
        recommendations = recommender.reactive_surprise_me(context)

        if not recommendations:
            return "I'm still figuring out your taste. Give me a clue — any cuisine you're curious about?"

        return shape_response(recommendations, self.context.channel, greeting="🎲 Something different:")

    async def _handle_friday(self) -> str:
        """Scenario 2: 'It's Friday' — proactive biryani suggestion.

        Friday biryani is one of the strongest food habits in Indian culture.
        The agent detects this pattern and reinforces it.
        """
        assert self.dna is not None
        recommender = Recommender(self.dna)
        now = datetime.now()
        friday_rec = recommender.proactive_friday_biryani(now.weekday(), now.hour)

        if friday_rec:
            if self.context.channel == "voice":
                return "Friday vibes! Your usual biryani from Meghana Foods? Want me to order?"
            else:
                return (
                    "🎉 **It's Friday!**\n\n"
                    "Your usual **biryani** — because Friday deserves a celebration.\n\n"
                    "Shall I order from your favorite spot?"
                )

        # Not a biryani person — general Friday suggestion
        return await self._handle_order_something()

    async def _handle_plan_evening(self) -> str:
        """Scenario 3: 'Plan my evening' — Dineout + Food cross-server.

        This is the Food DNA Agent's unique capability — combining signals
        from Food, Instamart, and Dineout that no single server provides.
        """
        assert self._mcp is not None and self.dna is not None

        parts = []

        # Step 1: Check for Dineout options
        try:
            locations = await self._mcp.dineout("get_saved_locations")
            saved_locs = locations.get("locations", [])
            if saved_locs:
                lat = saved_locs[0].get("lat", 0)
                lng = saved_locs[0].get("lng", 0)

                # Search for restaurants
                dineout_resp = await self._mcp.dineout("search_restaurants_dineout", {
                    "query": "dinner",
                    "lat": lat,
                    "lng": lng,
                })
                restaurants = dineout_resp.get("restaurants", [])

                if restaurants:
                    top = restaurants[0]
                    parts.append(
                        f"🍽️ **Dineout option:** {top.get('name', 'Restaurant')} "
                        f"— {top.get('rating', 'N/A')}⭐"
                    )

                    # Check slots
                    today = datetime.now().strftime("%Y-%m-%d")
                    try:
                        slots = await self._mcp.dineout("get_available_slots", {
                            "restaurantId": top.get("restaurantId", ""),
                            "date": today,
                        })
                        dinner_slots = slots.get("slots", {}).get("dinner", [])
                        if dinner_slots:
                            parts.append(f"   Available at {dinner_slots[0].get('time', '7:30 PM')}")
                    except MCPError:
                        pass
        except MCPError as e:
            logger.warning("Dineout search failed: %s", e)

        # Step 2: Food delivery option for later
        recommender = Recommender(self.dna)
        context = self._build_context()
        food_recs = recommender.reactive_order_something(context)
        if food_recs:
            parts.append(
                f"\n🍕 **Or order in:** {food_recs[0].name}"
                + (f" from {food_recs[0].restaurant}" if food_recs[0].restaurant else "")
            )

        if not parts:
            return "Let me find some options for your evening. Where are you located?"

        return "\n".join(parts)

    async def _handle_festival(self, intent: str) -> str:
        """Scenario 5: Festival-aware suggestions (Diwali, Holi, etc.).

        Indian festivals have specific food associations — the agent
        leverages cultural psychology to suggest timely, identity-affirming food.
        """
        assert self.dna is not None

        # Detect which festival
        festival_name = None
        for name in FESTIVAL_CALENDAR:
            if name in intent:
                festival_name = name
                break

        if not festival_name:
            festival_name = "diwali"  # Default

        recommender = Recommender(self.dna)
        festival_rec = recommender.proactive_festival(festival_name)

        if festival_rec:
            foods = FESTIVAL_CALENDAR[festival_name]["foods"]
            food_list = ", ".join(f.replace("_", " ").title() for f in foods[:3])

            if self.context.channel == "voice":
                return f"{festival_name.title()} vibes! How about traditional {foods[0].replace('_', ' ')}?"
            else:
                return (
                    f"🪔 **{festival_name.title()} Special!**\n\n"
                    f"Traditional {food_list} — perfect for the celebration.\n\n"
                    f"Shall I find the best options near you?"
                )

        return f"Happy {festival_name.title()}! 🪔 What would you like to order for the celebration?"

    async def _handle_restaurant_closed(self, restaurant_name: str) -> str:
        """Scenario 4: Restaurant closed → error recovery with alternatives.

        Cross-references Food DNA to find similar restaurants.
        """
        assert self._mcp is not None and self.dna is not None

        if not restaurant_name:
            return "Which restaurant is closed? I'll find you similar alternatives."

        # Search for alternatives
        try:
            search_resp = await self._mcp.food("search_restaurants", {
                "query": restaurant_name,
                "addressId": self.context.current_address_id or "",
            })
            available = [
                r for r in search_resp.get("restaurants", [])
                if r.get("availabilityStatus") == "OPEN"
            ]
        except MCPError:
            available = []

        if available:
            recommender = Recommender(self.dna)
            context = self._build_context()
            alternatives = recommender.cross_server_restaurant_closed(
                restaurant_name, available, context
            )

            if alternatives:
                return shape_response(
                    alternatives,
                    self.context.channel,
                    greeting=f"😔 {restaurant_name} is closed. But here are similar options:",
                )

        return (
            f"😔 {restaurant_name} is closed right now.\n\n"
            "Want me to search for something similar, or would you prefer a different cuisine?"
        )

    # -- proactive nudge (called by scheduler) -------------------------------

    async def check_proactive_nudges(self) -> list[str]:
        """Check for proactive nudge opportunities.

        Called periodically (e.g., via cron or heartbeat) to check if
        the agent should suggest food proactively.
        """
        assert self.dna is not None
        nudges: list[str] = []
        now = datetime.now()
        current_hour = now.hour

        nudge_engine = NudgeEngine(self.dna, self._nudge_state)
        recommender = Recommender(self.dna)

        # 1. Time-based nudge
        time_rec = recommender.proactive_time_based(current_hour)
        if time_rec:
            msg = nudge_engine.build_decision_fatigue_nudge(
                time_rec.name, time_rec.restaurant, current_hour
            )
            if msg:
                nudges.append(msg)

        # 2. Friday biryani
        friday_rec = recommender.proactive_friday_biryani(now.weekday(), current_hour)
        if friday_rec:
            msg = nudge_engine.build_habit_nudge(
                {"cue": "friday evening", "item": friday_rec.name},
                current_hour,
            )
            if msg:
                nudges.append(msg)

        # 3. Festival
        for festival_name, festival_data in FESTIVAL_CALENDAR.items():
            # Simple date check (production would use proper calendar)
            msg = nudge_engine.build_festival_nudge(
                festival_name, festival_data["foods"], current_hour
            )
            if msg:
                nudges.append(msg)

        # 4. Rain check
        if self.context.is_raining:
            rain_rec = recommender.proactive_rain(True)
            if rain_rec:
                msg = nudge_engine.build_emotional_nudge(
                    rain_rec.name, "", current_hour
                )
                if msg:
                    nudges.append(msg)

        return nudges

    # -- helpers -------------------------------------------------------------

    def _build_context(self) -> dict[str, Any]:
        """Build context dict for scoring functions."""
        now = datetime.now()
        return {
            "hour": self.context.current_hour or now.hour,
            "day_of_week": self.context.day_of_week or now.weekday(),
            "is_raining": self.context.is_raining,
            "party_size": self.context.party_size,
            "channel": self.context.channel,
            "address_id": self.context.current_address_id,
        }

    def _get_greeting(self) -> str:
        """Generate a time-appropriate greeting."""
        hour = self.context.current_hour or datetime.now().hour
        if 6 <= hour < 12:
            return "🌅 Good morning! Here's what I'd suggest for breakfast:"
        if 12 <= hour < 16:
            return "☀️ Lunch time! Here are your personalized picks:"
        if 16 <= hour < 18:
            return "🫖 Snack time! Quick bites for you:"
        if 18 <= hour < 22:
            return "🌙 Dinner time! Here's what looks good:"
        return "🌙 Late night cravings? Here are some options:"


# ---------------------------------------------------------------------------
# Convenience: run a quick demo
# ---------------------------------------------------------------------------

async def run_demo(config: Optional[Config] = None) -> None:
    """Run a quick demo of the agent (for testing).

    In a real deployment, this would be replaced by the actual
    voice/chat interface.
    """
    logging.basicConfig(level=logging.INFO)

    async with FoodDNAAgent(config) as agent:
        print("🔑 Starting OAuth flow...")
        url, verifier, state = agent.get_auth_url()
        print(f"   Visit: {url}")
        print(f"   (In production, user authenticates via browser)")

        # For demo, simulate with a mock token
        agent._mcp.set_access_token("demo_token", 432_000)
        print("   ✅ Using demo token")

        # Build profile
        print("\n📊 Building Food DNA profile...")
        dna = await agent.build_profile()
        print(f"   Data points: {dna.data_points}")
        print(f"   Confidence: {dna.confidence_score:.2f}")
        print(f"   Dietary: {dna.dietary_identity.primary.value}")
        print(f"   Top cuisine: {max(dna.cuisine_preferences, key=dna.cuisine_preferences.get)}")

        # Demo scenarios
        print("\n" + "=" * 60)
        print("DEMO SCENARIOS")
        print("=" * 60)

        scenarios = [
            ("order my usual", "Scenario 1: Behavioral lookup"),
            ("it's friday", "Scenario 2: Friday biryani"),
            ("plan my evening", "Scenario 3: Cross-server"),
            ("diwali tomorrow", "Scenario 5: Festival awareness"),
            ("something healthy", "Health-filtered recommendation"),
            ("surprise me", "Controlled novelty"),
        ]

        for intent, description in scenarios:
            print(f"\n--- {description} ---")
            print(f"User: \"{intent}\"")
            try:
                response = await agent.handle_intent(intent)
                print(f"Agent: {response}")
            except Exception as e:
                print(f"Agent: [Error: {e}]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demo())
