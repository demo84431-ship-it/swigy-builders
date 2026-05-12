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


def extract_from_search_menu(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from search_menu response.

    Reveals what dishes users search for across restaurants —
    the discovery signal that complements order history.
    """
    results = response.get("results", response.get("items", []))
    if not results:
        return {"search_menu_count": 0}

    features: dict[str, Any] = {"search_menu_count": len(results)}

    # Dish names searched
    dish_names = []
    cuisine_counter: Counter[str] = Counter()
    prices: list[float] = []
    dietary_signals: Counter[str] = Counter()

    non_veg_keywords = {"chicken", "mutton", "fish", "prawn", "egg", "beef", "pork", "lamb", "meat"}
    veg_keywords = {"paneer", "dal", "aloo", "gobi", "mushroom", "soya", "palak"}

    for item in results:
        name = item.get("name", "") or item.get("dishName", "")
        if name:
            dish_names.append(name)
            cuisine_counter[_cuisine_from_name(name)] += 1

            name_lower = name.lower()
            if any(kw in name_lower for kw in non_veg_keywords):
                dietary_signals["non_veg"] += 1
            elif any(kw in name_lower for kw in veg_keywords):
                dietary_signals["veg"] += 1

        price = _safe_float(item.get("price") or item.get("finalPrice"))
        if price > 0:
            prices.append(price)

        # Popularity score if available
        popularity = _safe_float(item.get("popularity") or item.get("rating"))
        if popularity > 0:
            features.setdefault("popularity_scores", []).append(popularity)

    # Cuisine distribution from search
    total_cuisines = sum(cuisine_counter.values()) or 1
    features["search_cuisine_distribution"] = {k: v / total_cuisines for k, v in cuisine_counter.items()}

    # Price range of searched items
    if prices:
        features["search_price_min"] = min(prices)
        features["search_price_max"] = max(prices)
        features["search_price_avg"] = sum(prices) / len(prices)

    # Dietary signals from search terms
    total_dietary = sum(dietary_signals.values()) or 1
    features["search_dietary_signals"] = {k: v / total_dietary for k, v in dietary_signals.items()}

    features["searched_dishes"] = dish_names[:20]

    return features


def extract_from_get_restaurant_menu(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from get_restaurant_menu response.

    Reveals browsing behavior — what sections they look at,
    what price ranges they consider, variant preferences.
    """
    sections = response.get("sections", response.get("categories", []))
    items = response.get("items", [])
    features: dict[str, Any] = {}

    # If flat items list, extract sections from it
    if not sections and items:
        section_names = set()
        for item in items:
            cat = item.get("category", item.get("section", ""))
            if cat:
                section_names.add(cat)
        sections = [{"name": s} for s in section_names]

    features["sections_browsed"] = [s.get("name", "") for s in sections if s.get("name")]
    features["section_count"] = len(sections)

    # Price range of viewed items
    all_items = items
    if not all_items:
        # Flatten sections into items
        for section in sections:
            all_items.extend(section.get("items", []))

    prices = [_safe_float(item.get("price") or item.get("finalPrice")) for item in all_items]
    prices = [p for p in prices if p > 0]
    if prices:
        features["menu_price_min"] = min(prices)
        features["menu_price_max"] = max(prices)
        features["menu_price_avg"] = sum(prices) / len(prices)

    # Variant preferences (veg/non-veg, size)
    variant_counter: Counter[str] = Counter()
    for item in all_items:
        is_veg = item.get("isVeg", item.get("veg", None))
        if is_veg is True:
            variant_counter["veg"] += 1
        elif is_veg is False:
            variant_counter["non_veg"] += 1

        # Size variants
        variants = item.get("variants", item.get("sizes", []))
        if variants:
            for v in variants:
                size = v.get("name", v.get("size", ""))
                if size:
                    variant_counter[f"size_{size.lower()}"] += 1

    total_variants = sum(variant_counter.values()) or 1
    features["variant_distribution"] = {k: v / total_variants for k, v in variant_counter.items()}

    # Add-on patterns
    add_on_count = 0
    for item in all_items:
        addons = item.get("addons", item.get("addOns", item.get("customizations", [])))
        if addons:
            add_on_count += len(addons)
    features["total_addons_available"] = add_on_count
    features["avg_addons_per_item"] = add_on_count / max(len(all_items), 1)

    return features


def extract_from_fetch_food_coupons_enhanced(response: dict[str, Any]) -> dict[str, Any]:
    """Enhanced coupon extraction.

    Extracts: coupon types (percentage vs flat), minimum order values,
    restaurant-specific vs platform coupons, expiry urgency.
    """
    coupons = response.get("coupons", response.get("couponsList", []))
    if not coupons:
        return {"enhanced_coupon_count": 0}

    features: dict[str, Any] = {"enhanced_coupon_count": len(coupons)}

    # Coupon types: percentage vs flat
    type_counter: Counter[str] = Counter()
    min_order_values: list[float] = []
    scope_counter: Counter[str] = Counter()
    urgency_counter: Counter[str] = Counter()

    for coupon in coupons:
        # Type detection
        discount_type = coupon.get("discountType", coupon.get("type", ""))
        if not discount_type:
            # Infer from fields
            if coupon.get("discountPercent") or coupon.get("percentage"):
                discount_type = "percentage"
            elif coupon.get("flatDiscount") or coupon.get("discountValue"):
                discount_type = "flat"
            else:
                discount_type = "unknown"
        type_counter[discount_type] += 1

        # Minimum order value
        min_order = _safe_float(coupon.get("minOrderValue") or coupon.get("minimumOrder"))
        if min_order > 0:
            min_order_values.append(min_order)

        # Scope: restaurant-specific vs platform
        restaurant_id = coupon.get("restaurantId", coupon.get("restaurantSpecific", ""))
        if restaurant_id:
            scope_counter["restaurant_specific"] += 1
        else:
            scope_counter["platform_wide"] += 1

        # Expiry urgency
        expiry = coupon.get("expiryDate", coupon.get("expiresAt", ""))
        if expiry:
            try:
                exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                days_left = (exp_dt - datetime.now(timezone.utc)).days
                if days_left <= 0:
                    urgency_counter["expired"] += 1
                elif days_left <= 1:
                    urgency_counter["expires_today"] += 1
                elif days_left <= 3:
                    urgency_counter["expires_soon"] += 1
                else:
                    urgency_counter["no_urgency"] += 1
            except (ValueError, TypeError):
                urgency_counter["unknown_expiry"] += 1

    total_coupons = len(coupons) or 1
    features["coupon_type_distribution"] = {k: v / total_coupons for k, v in type_counter.items()}
    features["coupon_scope_distribution"] = {k: v / total_coupons for k, v in scope_counter.items()}
    features["coupon_urgency_distribution"] = {k: v / total_coupons for k, v in urgency_counter.items()}

    if min_order_values:
        features["avg_min_order_value"] = sum(min_order_values) / len(min_order_values)
        features["min_order_range"] = (min(min_order_values), max(min_order_values))

    # Deal-seeking intensity: how many coupons are percentage-based (generally better deals)
    pct_ratio = type_counter.get("percentage", 0) / total_coupons
    features["percentage_coupon_ratio"] = pct_ratio

    return features


def extract_from_search_products(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from Instamart search_products response.

    Reveals grocery discovery intent — what products they're looking for
    beyond their go-to items.
    """
    products = response.get("products", response.get("items", []))
    if not products:
        return {"search_product_count": 0}

    features: dict[str, Any] = {"search_product_count": len(products)}

    # Product categories searched
    categories: Counter[str] = Counter()
    brands: Counter[str] = Counter()
    prices: list[float] = []

    for product in products:
        cat = product.get("category", product.get("subCategory", "other"))
        categories[cat] += 1

        brand = product.get("brand", "")
        if brand:
            brands[brand] += 1

        price = _safe_float(product.get("price") or product.get("discountedPrice"))
        if price > 0:
            prices.append(price)

    total_cats = sum(categories.values()) or 1
    features["product_category_distribution"] = {k: v / total_cats for k, v in categories.items()}

    # Price sensitivity: ratio of discounted/low-price items searched
    if prices:
        features["search_product_price_avg"] = sum(prices) / len(prices)
        features["search_product_price_min"] = min(prices)
        features["search_product_price_max"] = max(prices)

    # Brand preferences
    total_brands = sum(brands.values()) or 1
    features["search_brand_distribution"] = {k: v / total_brands for k, v in brands.most_common(10)}
    features["unique_brands_searched"] = len(brands)

    # Price sensitivity signal: if user searches for budget items
    if prices:
        budget_threshold = 100  # ₹100 as budget threshold for groceries
        budget_items = sum(1 for p in prices if p < budget_threshold)
        features["budget_product_ratio"] = budget_items / len(prices)

    return features


def extract_from_get_food_order_details(response: dict[str, Any]) -> dict[str, Any]:
    """Extract features from get_food_order_details response.

    Detailed order info — item-level data, delivery time accuracy,
    payment method preferences.
    """
    order = response.get("order", response)
    if not order:
        return {"order_detail_available": False}

    features: dict[str, Any] = {"order_detail_available": True}

    # Actual items ordered
    items = order.get("items", [])
    item_names = []
    for item in items:
        name = item.get("name", "") if isinstance(item, dict) else str(item)
        if name:
            item_names.append(name)
    features["detail_items"] = item_names
    features["detail_item_count"] = len(item_names)

    # Delivery time: actual vs estimated
    estimated_time = _safe_float(order.get("estimatedDeliveryTime") or order.get("eta"))
    actual_time = _safe_float(order.get("actualDeliveryTime") or order.get("deliveredIn"))
    if estimated_time > 0 and actual_time > 0:
        features["delivery_time_delta"] = actual_time - estimated_time
        features["delivery_time_accuracy"] = 1.0 - min(abs(actual_time - estimated_time) / max(estimated_time, 1), 1.0)
    elif estimated_time > 0:
        features["estimated_delivery_time"] = estimated_time

    # Payment method
    payment = order.get("paymentMethod", order.get("payment", {}))
    if isinstance(payment, dict):
        method = payment.get("method", payment.get("type", ""))
    else:
        method = str(payment)
    if method:
        features["payment_method"] = method

    # Tip behavior
    tip = _safe_float(order.get("tip") or order.get("tipAmount"))
    features["tip_amount"] = tip
    features["tipped"] = tip > 0

    # Rating given
    rating = _safe_float(order.get("rating") or order.get("userRating"))
    if rating > 0:
        features["order_rating"] = rating

    # Order total
    total = _safe_float(order.get("total") or order.get("orderTotal") or order.get("amount"))
    if total > 0:
        features["order_total"] = total

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
        "search_menu": extract_from_search_menu,
        "get_restaurant_menu": extract_from_get_restaurant_menu,
        "fetch_food_coupons_enhanced": extract_from_fetch_food_coupons_enhanced,
        "search_products": extract_from_search_products,
        "get_food_order_details": extract_from_get_food_order_details,
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
