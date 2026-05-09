"""
Food DNA Agent — Feature Extraction

Extracts behavioral signals from MCP tool responses and maps them to
Food DNA dimensions. Each extractor handles a specific MCP tool and
returns a normalized feature dict.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _normalize(dist: dict[str, float]) -> dict[str, float]:
    """Normalize a distribution so values sum to 1.0."""
    total = sum(dist.values())
    if total == 0:
        return dist
    return {k: v / total for k, v in dist.items()}


def _cuisine_from_name(name: str) -> str:
    """Heuristic: map a restaurant/dish name to a cuisine category.

    Production version would use a trained classifier or restaurant metadata.
    This is a simplified keyword-based fallback.
    """
    name_lower = name.lower()
    if any(w in name_lower for w in ["dosa", "idli", "vada", "sambar", "uttapam", "bisi bele"]):
        return "south_indian"
    if any(w in name_lower for w in ["biryani", "tikka", "naan", "butter chicken", "rajma", "paratha"]):
        return "north_indian"
    if any(w in name_lower for w in ["manchurian", "noodle", "chowmein", "fried rice", "schezwan"]):
        return "chinese"
    if any(w in name_lower for w in ["pizza", "pasta", "burger", "sandwich"]):
        return "italian"
    if any(w in name_lower for w in ["roll", "chaat", "pani puri", "samosa", "pakora", "vada pav"]):
        return "street_food"
    if any(w in name_lower for w in ["cake", "ice cream", "sweet", "mithai", "halwa", "gulab"]):
        return "dessert"
    if any(w in name_lower for w in ["salad", "protein", "oat", "smoothie", "healthy"]):
        return "healthy"
    return "other"


# ---------------------------------------------------------------------------
# Extractors — one per MCP tool
# ---------------------------------------------------------------------------

def extract_from_food_orders(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from get_food_orders response.

    This is the primary signal source — informs all 10 dimensions.
    """
    orders = response.get("orders", [])
    if not orders:
        return {"order_count": 0}

    features: dict[str, Any] = {"order_count": len(orders)}

    # Temporal patterns
    hours = [0.0] * 24
    days = [0.0] * 7
    timestamps = []
    for order in orders:
        ts_str = order.get("timestamp") or order.get("createdAt") or order.get("orderDate")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                hours[ts.hour] += 1
                days[ts.weekday()] += 1
                timestamps.append(ts)
            except (ValueError, TypeError):
                pass

    total_time_orders = sum(hours) or 1
    features["hour_distribution"] = [h / total_time_orders for h in hours]
    total_day_orders = sum(days) or 1
    features["day_distribution"] = [d / total_day_orders for d in days]
    features["late_night_ratio"] = sum(hours[22:] + hours[:2]) / total_time_orders
    features["weekend_ratio"] = (days[5] + days[6]) / total_day_orders

    # Order interval
    if len(timestamps) >= 2:
        timestamps.sort()
        intervals = [(timestamps[i + 1] - timestamps[i]).total_seconds() / 86400 for i in range(len(timestamps) - 1)]
        features["order_interval_days"] = sum(intervals) / len(intervals)
    else:
        features["order_interval_days"] = 3.0

    # Cuisine distribution
    cuisine_counter: Counter[str] = Counter()
    for order in orders:
        items = order.get("items", [])
        restaurant_name = order.get("restaurantName", "")
        if restaurant_name:
            cuisine_counter[_cuisine_from_name(restaurant_name)] += 1
        for item in items:
            item_name = item.get("name", "") if isinstance(item, dict) else str(item)
            cuisine_counter[_cuisine_from_name(item_name)] += 1

    total_cuisines = sum(cuisine_counter.values()) or 1
    features["cuisine_distribution"] = {k: v / total_cuisines for k, v in cuisine_counter.items()}

    # Price psychology
    totals = [_safe_float(o.get("total") or o.get("orderTotal") or o.get("amount")) for o in orders]
    totals = [t for t in totals if t > 0]
    if totals:
        features["avg_order_value"] = sum(totals) / len(totals)
        if len(totals) > 1:
            mean = features["avg_order_value"]
            features["aov_std"] = (sum((t - mean) ** 2 for t in totals) / (len(totals) - 1)) ** 0.5
        else:
            features["aov_std"] = 0.0

    # Restaurant concentration (Herfindahl index)
    restaurant_counter: Counter[str] = Counter()
    for order in orders:
        rid = order.get("restaurantId") or order.get("restaurantName", "unknown")
        restaurant_counter[rid] += 1
    total_rest_orders = sum(restaurant_counter.values()) or 1
    hhi = sum((c / total_rest_orders) ** 2 for c in restaurant_counter.values())
    features["restaurant_concentration"] = hhi  # 0 = evenly spread, 1 = all from one place

    # Item concentration
    item_counter: Counter[str] = Counter()
    for order in orders:
        for item in order.get("items", []):
            name = item.get("name", "") if isinstance(item, dict) else str(item)
            if name:
                item_counter[name] += 1
    total_item_orders = sum(item_counter.values()) or 1
    features["item_concentration"] = sum((c / total_item_orders) ** 2 for c in item_counter.values())

    # Top items and restaurants for habit detection
    features["top_items"] = [name for name, _ in item_counter.most_common(10)]
    features["top_restaurants"] = [name for name, _ in restaurant_counter.most_common(5)]

    # Social dynamics (estimate from order size)
    item_counts = [len(o.get("items", [])) for o in orders]
    avg_items = sum(item_counts) / len(item_counts) if item_counts else 1
    features["avg_items_per_order"] = avg_items

    # Dietary signal: check for non-veg items
    non_veg_keywords = {"chicken", "mutton", "fish", "prawn", "egg", "beef", "pork", "lamb"}
    veg_keywords = {"paneer", "dal", "aloo", "gobi", "mushroom", "soya"}
    non_veg_count = 0
    veg_count = 0
    for order in orders:
        for item in order.get("items", []):
            name = (item.get("name", "") if isinstance(item, dict) else str(item)).lower()
            if any(kw in name for kw in non_veg_keywords):
                non_veg_count += 1
            if any(kw in name for kw in veg_keywords):
                veg_count += 1
    features["non_veg_ratio"] = non_veg_count / max(non_veg_count + veg_count, 1)

    return features


def extract_from_go_to_items(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from your_go_to_items (Instamart) response.

    Reveals grocery patterns, brand loyalty, dietary identity.
    """
    items = response.get("items", [])
    if not items:
        return {"go_to_count": 0}

    features: dict[str, Any] = {"go_to_count": len(items)}

    # Category distribution
    categories: Counter[str] = Counter()
    brands: Counter[str] = Counter()
    for item in items:
        cat = item.get("category", "other")
        categories[cat] += 1
        brand = item.get("brand", "")
        if brand:
            brands[brand] += 1

    total_cats = sum(categories.values()) or 1
    features["category_distribution"] = {k: v / total_cats for k, v in categories.items()}
    features["top_brands"] = [b for b, _ in brands.most_common(5)]

    # Brand concentration (loyalty)
    total_brands = sum(brands.values()) or 1
    features["brand_concentration"] = sum((c / total_brands) ** 2 for c in brands.values())

    # Dietary signal from grocery items
    item_names = [item.get("name", "").lower() for item in items]
    non_veg_grocery = sum(1 for n in item_names if any(kw in n for kw in ["chicken", "mutton", "fish", "egg", "meat"]))
    features["grocery_non_veg_ratio"] = non_veg_grocery / max(len(item_names), 1)

    # Health signal
    healthy_keywords = {"organic", "sugar free", "low fat", "multigrain", "oats", "quinoa", "protein"}
    unhealthy_keywords = {"chips", "cookies", "chocolate", "soda", "fries", "instant noodle"}
    healthy_count = sum(1 for n in item_names if any(kw in n for kw in healthy_keywords))
    unhealthy_count = sum(1 for n in item_names if any(kw in n for kw in unhealthy_keywords))
    total_health = healthy_count + unhealthy_count
    features["grocery_health_score"] = healthy_count / max(total_health, 1)

    # Regional staples detection
    regional_keywords = {
        "rice": "rice_dominant",
        "atta": "wheat_dominant",
        "dal": "indian_staple",
        "ghee": "indian_staple",
        "curd": "indian_staple",
        "idli": "south_indian",
        "dosa": "south_indian",
        "paratha": "north_indian",
    }
    regional_signals: Counter[str] = Counter()
    for n in item_names:
        for kw, signal in regional_keywords.items():
            if kw in n:
                regional_signals[signal] += 1
    features["regional_signals"] = dict(regional_signals)

    return features


def extract_from_booking_status(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from get_booking_status (Dineout) response.

    Reveals social dynamics, occasion types, dining frequency.
    """
    bookings = response.get("bookings", [])
    if not bookings:
        return {"booking_count": 0}

    features: dict[str, Any] = {"booking_count": len(bookings)}

    # Party sizes
    party_sizes = [_safe_float(b.get("partySize", 1)) for b in bookings]
    party_sizes = [p for p in party_sizes if p > 0]
    if party_sizes:
        features["avg_party_size"] = sum(party_sizes) / len(party_sizes)
        features["max_party_size"] = max(party_sizes)

    # Occasion detection
    occasions: Counter[str] = Counter()
    for b in bookings:
        occasion = b.get("occasion", b.get("specialRequest", ""))
        if occasion:
            occasions[occasion.lower()] += 1
    features["occasion_types"] = dict(occasions)

    # Price range from bookings
    totals = [_safe_float(b.get("totalAmount") or b.get("amount")) for b in bookings]
    totals = [t for t in totals if t > 0]
    if totals:
        features["dining_avg_spend"] = sum(totals) / len(totals)

    return features


def extract_from_addresses(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from get_addresses response.

    Reveals life stage, social dynamics, regional context.
    """
    addresses = response.get("addresses", [])
    if not addresses:
        return {"address_count": 0}

    features: dict[str, Any] = {"address_count": len(addresses)}

    # Address labels
    labels = [a.get("label", "").lower() for a in addresses]
    features["has_home"] = any("home" in l for l in labels)
    features["has_work"] = any(w in l for w in ["work", "office", "company"])
    features["has_other"] = any(l for l in labels if l not in ("home", "work", "office", "company"))

    # Multi-city detection
    cities = set()
    for a in addresses:
        addr_text = a.get("address", "") or a.get("fullAddress", "")
        # Simple city extraction (production would use geocoding)
        parts = addr_text.split(",")
        if len(parts) >= 2:
            cities.add(parts[-2].strip().lower())
    features["multi_city"] = len(cities) > 1

    return features


def extract_from_search_restaurants(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from search_restaurants response.

    Reveals cuisine preferences, price range, exploration signals.
    """
    restaurants = response.get("restaurants", [])
    if not restaurants:
        return {"search_result_count": 0}

    features: dict[str, Any] = {"search_result_count": len(restaurants)}

    # Cuisine distribution of search results
    cuisines: Counter[str] = Counter()
    for r in restaurants:
        for c in r.get("cuisines", []):
            cuisines[c.lower()] += 1
    total_cuisines = sum(cuisines.values()) or 1
    features["search_cuisine_distribution"] = {k: v / total_cuisines for k, v in cuisines.items()}

    # Price range
    prices = [_safe_float(r.get("priceForTwo") or r.get("avgCost")) for r in restaurants]
    prices = [p for p in prices if p > 0]
    if prices:
        features["search_avg_price"] = sum(prices) / len(prices)

    # Open vs closed
    open_count = sum(1 for r in restaurants if r.get("availabilityStatus") == "OPEN")
    features["open_ratio"] = open_count / len(restaurants)

    return features


def extract_from_coupons(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from fetch_food_coupons response.

    Reveals price psychology (deal-seeking behavior).
    """
    coupons = response.get("coupons", [])
    features: dict[str, Any] = {"available_coupons": len(coupons)}

    # Discount levels
    discounts = [_safe_float(c.get("discountValue") or c.get("maxDiscount")) for c in coupons]
    discounts = [d for d in discounts if d > 0]
    if discounts:
        features["avg_coupon_discount"] = sum(discounts) / len(discounts)
        features["max_coupon_discount"] = max(discounts)

    return features


# ---------------------------------------------------------------------------
# Aggregate extractor
# ---------------------------------------------------------------------------

def extract_all_features(mcp_responses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Run all extractors on a batch of MCP responses.

    Args:
        mcp_responses: Dict mapping tool_name → response dict.
            e.g., {"get_food_orders": {...}, "your_go_to_items": {...}}

    Returns:
        Merged feature dict from all extractors.
    """
    extractors = {
        "get_food_orders": extract_from_food_orders,
        "your_go_to_items": extract_from_go_to_items,
        "get_booking_status": extract_from_booking_status,
        "get_addresses": extract_from_addresses,
        "search_restaurants": extract_from_search_restaurants,
        "fetch_food_coupons": extract_from_coupons,
    }

    all_features: dict[str, Any] = {}
    for tool_name, response in mcp_responses.items():
        extractor = extractors.get(tool_name)
        if extractor:
            try:
                features = extractor(response)
                all_features.update(features)
            except Exception as e:
                logger.warning("Feature extraction failed for %s: %s", tool_name, e)
        else:
            logger.debug("No extractor for tool: %s", tool_name)

    return all_features
