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
    extract_from_search_menu,
    extract_from_get_restaurant_menu,
    extract_from_fetch_food_coupons_enhanced,
    extract_from_search_products,
    extract_from_get_food_order_details,
)
from .food_dna import ChangeStage, FoodDNA
from .food_dna_calculator import FoodDNACalculator
from .mcp_client import MCPClient, MCPError, ErrorBucket
from .nudge_engine import NudgeEngine, SuppressionState
from .cart_manager import CartManager
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
        self._cart_manager = CartManager()
        self._session_id: str = ""

    async def __aenter__(self) -> "FoodDNAAgent":
        self._mcp = MCPClient(self._config, session_id=self._session_id or None)
        await self._mcp.__aenter__()
        self._session_id = self._mcp._session_id
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

        # Tool routing for new MCP tools
        if any(phrase in intent_lower for phrase in ["search menu", "find biryani", "search biryani", "best biryani"]):
            return await self._handle_search_menu(intent_lower)
        if any(phrase in intent_lower for phrase in ["show me coupons", "coupons", "any deals", "discount", "offers"]):
            return await self._handle_fetch_coupons()
        if any(phrase in intent_lower for phrase in ["show me the menu", "restaurant menu", "what does", "menu of"]):
            return await self._handle_get_restaurant_menu(intent_lower, kwargs.get("restaurant_id", ""))
        if any(phrase in intent_lower for phrase in ["search products", "grocery", "instamart", "find product"]):
            return await self._handle_search_products(intent_lower)
        if any(phrase in intent_lower for phrase in ["order details", "order info", "order status"]):
            return await self._handle_order_details(kwargs.get("order_id", ""))

        # Cart management
        if any(phrase in intent_lower for phrase in ["add to cart", "add biryani", "order biryani"]):
            return await self._handle_add_to_cart(kwargs.get("item", {}))
        if any(phrase in intent_lower for phrase in ["checkout", "place order", "confirm order"]):
            return await self._handle_checkout()
        if any(phrase in intent_lower for phrase in ["clear cart", "empty cart"]):
            return self._handle_clear_cart()
        if any(phrase in intent_lower for phrase in ["view cart", "my cart", "show cart"]):
            return self._handle_view_cart()

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

    # -- new tool handlers --------------------------------------------------

    async def _handle_search_menu(self, query: str) -> str:
        """Handle search_menu — dish discovery across restaurants."""
        assert self._mcp is not None

        # Extract search term from query
        search_term = query
        for phrase in ["search menu", "find me", "best", "near me"]:
            search_term = search_term.replace(phrase, "")
        search_term = search_term.strip() or "biryani"

        try:
            result = await self._mcp.food("search_menu", {"query": search_term})

            # Extract features for Food DNA
            features = extract_from_search_menu(result)
            logger.info("search_menu extracted %d items", features.get("search_menu_count", 0))

            # Format response
            items = result.get("results", result.get("items", []))
            if not items:
                return f"I couldn't find '{search_term}' in any nearby restaurants. Want to try a different dish?"

            parts = [f"🔍 **Best {search_term.title()} Near You**\n"]
            for i, item in enumerate(items[:5], 1):
                name = item.get("name", item.get("dishName", ""))
                restaurant = item.get("restaurantName", item.get("restaurant", ""))
                price = item.get("price", item.get("finalPrice", ""))
                rating = item.get("rating", item.get("popularity", ""))
                parts.append(f"**{i}. {name}** — {restaurant}")
                meta_parts = []
                if price:
                    meta_parts.append(f"💰 ₹{int(float(price))}")
                if rating:
                    meta_parts.append(f"⭐ {rating}")
                if meta_parts:
                    parts.append(f"   {' · '.join(meta_parts)}")

            parts.append("\nWhich one catches your eye?")
            return "\n".join(parts)

        except MCPError as e:
            logger.warning("search_menu failed: %s", e)
            return f"I had trouble searching for '{search_term}'. Want me to try something else?"

    async def _handle_fetch_coupons(self) -> str:
        """Handle fetch_food_coupons — show available deals."""
        assert self._mcp is not None

        try:
            result = await self._mcp.food("fetch_food_coupons")

            # Extract features
            features = extract_from_fetch_food_coupons_enhanced(result)
            logger.info("fetch_food_coupons found %d coupons", features.get("enhanced_coupon_count", 0))

            coupons = result.get("coupons", result.get("couponsList", []))
            if not coupons:
                return "No coupons available right now. But your Food DNA shows you usually get great value anyway!"

            parts = ["🎟️ **Available Coupons**\n"]
            for i, coupon in enumerate(coupons[:5], 1):
                code = coupon.get("code", coupon.get("couponCode", f"DEAL{i}"))
                desc = coupon.get("description", coupon.get("title", ""))
                discount = coupon.get("discountValue", coupon.get("maxDiscount", ""))
                min_order = coupon.get("minOrderValue", coupon.get("minimumOrder", ""))

                parts.append(f"**🏷️ {code}**")
                if desc:
                    parts.append(f"   {desc}")
                meta_parts = []
                if discount:
                    meta_parts.append(f"Save ₹{int(float(discount))}")
                if min_order:
                    meta_parts.append(f"Min order ₹{int(float(min_order))}")
                if meta_parts:
                    parts.append(f"   {' · '.join(meta_parts)}")

            parts.append("\nWant me to apply one of these to your next order?")
            return "\n".join(parts)

        except MCPError as e:
            logger.warning("fetch_food_coupons failed: %s", e)
            return "I couldn't fetch coupons right now. Want me to search for deals on a specific restaurant?"

    async def _handle_get_restaurant_menu(self, query: str, restaurant_id: str) -> str:
        """Handle get_restaurant_menu — browse a specific restaurant's menu."""
        assert self._mcp is not None

        if not restaurant_id:
            # Try to extract restaurant name from query
            for phrase in ["show me the menu", "restaurant menu", "what does", "menu of"]:
                query = query.replace(phrase, "")
            restaurant_name = query.strip()
            if not restaurant_name:
                return "Which restaurant's menu would you like to see?"

            # Search for the restaurant first
            try:
                search_resp = await self._mcp.food("search_restaurants", {"query": restaurant_name})
                restaurants = search_resp.get("restaurants", [])
                if restaurants:
                    restaurant_id = restaurants[0].get("restaurantId", "")
                else:
                    return f"I couldn't find '{restaurant_name}'. Want to try a different name?"
            except MCPError:
                return f"I had trouble finding '{restaurant_name}'. Want me to try something else?"

        try:
            result = await self._mcp.food("get_restaurant_menu", {"restaurantId": restaurant_id})

            # Extract features
            features = extract_from_get_restaurant_menu(result)
            logger.info(
                "get_restaurant_menu: %d sections, price range ₹%.0f-₹%.0f",
                features.get("section_count", 0),
                features.get("menu_price_min", 0),
                features.get("menu_price_max", 0),
            )

            sections = features.get("sections_browsed", [])
            price_range = ""
            if features.get("menu_price_min") and features.get("menu_price_max"):
                price_range = f"💰 ₹{int(features['menu_price_min'])} – ₹{int(features['menu_price_max'])}"

            parts = ["📋 **Restaurant Menu**\n"]
            if sections:
                parts.append(f"Sections: {', '.join(sections[:8])}")
            if price_range:
                parts.append(price_range)

            # Show top items
            items = result.get("items", [])
            if items:
                parts.append("\n**Popular items:**")
                for i, item in enumerate(items[:6], 1):
                    name = item.get("name", "")
                    price = item.get("price", item.get("finalPrice", ""))
                    is_veg = "🟢" if item.get("isVeg") else "🔴" if item.get("isVeg") is False else ""
                    price_str = f"₹{int(float(price))}" if price else ""
                    parts.append(f"  {i}. {is_veg} {name} — {price_str}")

            parts.append("\nWhat would you like to add to your cart?")
            return "\n".join(parts)

        except MCPError as e:
            logger.warning("get_restaurant_menu failed: %s", e)
            return "I couldn't load the menu right now. Want me to try a different restaurant?"

    async def _handle_search_products(self, query: str) -> str:
        """Handle search_products (Instamart) — grocery discovery."""
        assert self._mcp is not None

        search_term = query
        for phrase in ["search products", "grocery", "instamart", "find product"]:
            search_term = search_term.replace(phrase, "")
        search_term = search_term.strip() or "milk"

        try:
            result = await self._mcp.instamart("search_products", {"query": search_term})

            # Extract features
            features = extract_from_search_products(result)
            logger.info("search_products found %d items", features.get("search_product_count", 0))

            products = result.get("products", result.get("items", []))
            if not products:
                return f"I couldn't find '{search_term}' on Instamart. Want to try a different product?"

            parts = [f"🛒 **Instamart: {search_term.title()}**\n"]
            for i, product in enumerate(products[:5], 1):
                name = product.get("name", "")
                brand = product.get("brand", "")
                price = product.get("price", product.get("discountedPrice", ""))
                parts.append(f"**{i}. {name}**" + (f" — {brand}" if brand else ""))
                if price:
                    parts.append(f"   💰 ₹{int(float(price))}")

            parts.append("\nWant me to add any of these to your Instamart cart?")
            return "\n".join(parts)

        except MCPError as e:
            logger.warning("search_products failed: %s", e)
            return f"I had trouble searching for '{search_term}' on Instamart. Want me to try something else?"

    async def _handle_order_details(self, order_id: str) -> str:
        """Handle get_food_order_details — detailed order info."""
        assert self._mcp is not None

        try:
            result = await self._mcp.food("get_food_order_details", {"orderId": order_id} if order_id else {})

            # Extract features
            features = extract_from_get_food_order_details(result)
            logger.info("get_food_order_details: %d items", features.get("detail_item_count", 0))

            if not features.get("order_detail_available"):
                return "I couldn't find that order. Do you have an order ID?"

            parts = ["📋 **Order Details**\n"]

            items = features.get("detail_items", [])
            if items:
                parts.append(f"Items: {', '.join(items[:5])}")

            if features.get("order_total"):
                parts.append(f"Total: ₹{int(features['order_total'])}")

            if features.get("delivery_time_delta") is not None:
                delta = features["delivery_time_delta"]
                if delta <= 0:
                    parts.append("✅ Delivered on time!")
                else:
                    parts.append(f"⏱️ Delivered {int(delta)} min late")

            if features.get("payment_method"):
                parts.append(f"Payment: {features['payment_method']}")

            if features.get("tipped"):
                parts.append(f"💝 Tipped ₹{int(features['tip_amount'])}")

            if features.get("order_rating"):
                parts.append(f"⭐ Your rating: {features['order_rating']}")

            return "\n".join(parts)

        except MCPError as e:
            logger.warning("get_food_order_details failed: %s", e)
            return "I couldn't fetch order details right now. Want me to check your recent orders instead?"

    # -- cart handlers -------------------------------------------------------

    async def _handle_add_to_cart(self, item: dict[str, Any]) -> str:
        """Add an item to the session cart."""
        session_id = self._session_id or "default"

        # Ensure we have a cart
        cart = self._cart_manager.get_cart(session_id)
        if not cart:
            # Start with a demo restaurant
            restaurant_id = item.get("restaurant_id", "rest_demo_001")
            restaurant_name = item.get("restaurant_name", "Restaurant")
            cart = self._cart_manager.start_cart(session_id, restaurant_id, restaurant_name)

        # Default item if none provided
        if not item or not item.get("name"):
            item = {"name": "Biryani", "price": 250, "quantity": 1}

        cart = self._cart_manager.add_item(session_id, item)
        summary = self._cart_manager.get_confirmation_summary(session_id)

        parts = [
            f"🛒 **Added to cart!**",
            f"Restaurant: {cart.restaurant_name}",
            f"",
            f"Items: {cart.item_count} · Total: ₹{cart.total:.0f}",
            f"",
            f"Say 'checkout' to place your order, or keep browsing!",
        ]
        return "\n".join(parts)

    async def _handle_checkout(self) -> str:
        """Handle checkout — confirm and place order."""
        session_id = self._session_id or "default"
        summary = self._cart_manager.get_confirmation_summary(session_id)

        if not summary.get("has_cart"):
            return "Your cart is empty! What would you like to order?"

        if summary.get("empty"):
            return "Your cart is empty! Add some items first."

        parts = [
            f"🛒 **Order Confirmation**",
            f"📍 {summary['restaurant_name']}",
            f"",
        ]
        parts.extend(summary["items"])
        parts.extend([
            f"",
            f"Subtotal: ₹{summary['subtotal']:.0f}",
            f"Delivery: ₹{summary['delivery_fee']:.0f}",
            f"**Total: ₹{summary['total']:.0f}**",
            f"",
            f"Shall I place the order? Say 'confirm' to proceed.",
        ])

        self.context.pending_confirmation = summary
        return "\n".join(parts)

    def _handle_clear_cart(self) -> str:
        """Clear the current cart."""
        session_id = self._session_id or "default"
        self._cart_manager.clear_cart(session_id)
        return "🗑️ Cart cleared! What would you like to order instead?"

    def _handle_view_cart(self) -> str:
        """View current cart."""
        session_id = self._session_id or "default"
        summary = self._cart_manager.get_confirmation_summary(session_id)

        if not summary.get("has_cart") or summary.get("empty"):
            return "Your cart is empty! What would you like to order?"

        return summary["formatted_summary"]

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
