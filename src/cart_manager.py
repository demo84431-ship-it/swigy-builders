"""
Food DNA Agent — Cart State Manager

Manages cart lifecycle across multi-turn conversations.
Cart is tied to a single restaurant per Swiggy's model.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CartState:
    """Represents the current cart for a session.

    Cart is single-restaurant per Swiggy's ordering model.
    Adding an item from a different restaurant flushes the existing cart.
    """

    session_id: str
    restaurant_id: str
    restaurant_name: str
    items: list[dict[str, Any]] = field(default_factory=list)  # [{name, quantity, price, variant}]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    delivery_fee: float = 0.0

    @property
    def subtotal(self) -> float:
        """Calculate subtotal from items."""
        return sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in self.items
        )

    @property
    def item_count(self) -> int:
        """Total number of items (respecting quantities)."""
        return sum(item.get("quantity", 1) for item in self.items)

    @property
    def total(self) -> float:
        """Subtotal + delivery fee."""
        return self.subtotal + self.delivery_fee

    def to_dict(self) -> dict[str, Any]:
        """Serialize cart state to dict."""
        return {
            "session_id": self.session_id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant_name,
            "items": self.items,
            "item_count": self.item_count,
            "subtotal": self.subtotal,
            "delivery_fee": self.delivery_fee,
            "total": self.total,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CartManager:
    """Manages cart lifecycle across multi-turn conversations.

    Each session gets one cart, tied to a single restaurant.
    Adding from a different restaurant automatically flushes the old cart.

    Usage:
        manager = CartManager()
        cart = manager.start_cart("sess_123", "rest_456", "Meghana Foods")
        cart = manager.add_item("sess_123", {"name": "Biryani", "price": 250})
        summary = manager.get_confirmation_summary("sess_123")
    """

    def __init__(self) -> None:
        self._carts: dict[str, CartState] = {}  # session_id -> cart

    def get_cart(self, session_id: str) -> Optional[CartState]:
        """Get current cart for a session. Returns None if no active cart."""
        return self._carts.get(session_id)

    def start_cart(
        self,
        session_id: str,
        restaurant_id: str,
        restaurant_name: str,
        delivery_fee: float = 0.0,
    ) -> CartState:
        """Start a new cart. Flushes any existing cart for a different restaurant.

        If the same restaurant, returns the existing cart.
        """
        existing = self._carts.get(session_id)
        if existing and existing.restaurant_id == restaurant_id:
            logger.debug("Reusing existing cart for session=%s restaurant=%s", session_id, restaurant_id)
            return existing

        if existing:
            logger.info(
                "Flushing cart for session=%s (switching from %s to %s)",
                session_id,
                existing.restaurant_name,
                restaurant_name,
            )

        cart = CartState(
            session_id=session_id,
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name,
            delivery_fee=delivery_fee,
        )
        self._carts[session_id] = cart
        logger.info("Started new cart for session=%s restaurant=%s", session_id, restaurant_name)
        return cart

    def add_item(self, session_id: str, item: dict[str, Any]) -> CartState:
        """Add item to cart. Returns updated cart.

        Item dict should have at minimum: name, price.
        Optional: quantity (default 1), variant, item_id.
        """
        cart = self._carts.get(session_id)
        if not cart:
            raise ValueError(f"No active cart for session {session_id}. Call start_cart first.")

        # Normalize item
        normalized = {
            "name": item.get("name", item.get("itemName", "Unknown")),
            "price": item.get("price", 0),
            "quantity": item.get("quantity", 1),
            "variant": item.get("variant", ""),
            "item_id": item.get("item_id", item.get("itemId", "")),
        }

        # Check if same item+variant already in cart → increment quantity
        for existing in cart.items:
            if (
                existing["name"].lower() == normalized["name"].lower()
                and existing.get("variant", "") == normalized.get("variant", "")
            ):
                existing["quantity"] = existing.get("quantity", 1) + normalized["quantity"]
                cart.updated_at = time.time()
                logger.info(
                    "Updated quantity for %s in cart session=%s (qty=%d)",
                    normalized["name"], session_id, existing["quantity"],
                )
                return cart

        # New item
        cart.items.append(normalized)
        cart.updated_at = time.time()
        logger.info(
            "Added %s (₹%.0f x%d) to cart session=%s",
            normalized["name"], normalized["price"], normalized["quantity"], session_id,
        )
        return cart

    def remove_item(self, session_id: str, item_name: str) -> CartState:
        """Remove item from cart by name.

        Returns updated cart. Raises ValueError if no cart or item not found.
        """
        cart = self._carts.get(session_id)
        if not cart:
            raise ValueError(f"No active cart for session {session_id}")

        item_name_lower = item_name.lower()
        for i, item in enumerate(cart.items):
            if item["name"].lower() == item_name_lower:
                removed = cart.items.pop(i)
                cart.updated_at = time.time()
                logger.info("Removed %s from cart session=%s", removed["name"], session_id)
                return cart

        raise ValueError(f"Item '{item_name}' not found in cart")

    def get_confirmation_summary(self, session_id: str) -> dict[str, Any]:
        """Generate confirmation summary before order placement.

        Returns items, subtotal, delivery fee, total, restaurant info.
        Designed to be shown to the user for final confirmation.
        """
        cart = self._carts.get(session_id)
        if not cart:
            return {"error": "No active cart", "has_cart": False}

        if not cart.items:
            return {"error": "Cart is empty", "has_cart": True, "empty": True}

        item_lines = []
        for item in cart.items:
            qty = item.get("quantity", 1)
            name = item.get("name", "Unknown")
            price = item.get("price", 0)
            variant = item.get("variant", "")
            line = f"{qty}x {name}"
            if variant:
                line += f" ({variant})"
            line += f" — ₹{price * qty:.0f}"
            item_lines.append(line)

        return {
            "has_cart": True,
            "empty": False,
            "restaurant_name": cart.restaurant_name,
            "restaurant_id": cart.restaurant_id,
            "items": item_lines,
            "item_count": cart.item_count,
            "subtotal": cart.subtotal,
            "delivery_fee": cart.delivery_fee,
            "total": cart.total,
            "formatted_summary": self._format_summary(cart),
        }

    def update_delivery_fee(self, session_id: str, fee: float) -> CartState:
        """Update the delivery fee for a cart."""
        cart = self._carts.get(session_id)
        if not cart:
            raise ValueError(f"No active cart for session {session_id}")
        cart.delivery_fee = fee
        cart.updated_at = time.time()
        return cart

    def clear_cart(self, session_id: str) -> None:
        """Clear the cart for a session."""
        if session_id in self._carts:
            logger.info("Cleared cart for session=%s", session_id)
            del self._carts[session_id]

    def list_active_carts(self) -> list[dict[str, Any]]:
        """List all active carts (for debugging/monitoring)."""
        return [
            {
                "session_id": sid,
                "restaurant": cart.restaurant_name,
                "item_count": cart.item_count,
                "total": cart.total,
            }
            for sid, cart in self._carts.items()
        ]

    @staticmethod
    def _format_summary(cart: CartState) -> str:
        """Format a human-readable confirmation summary."""
        lines = [f"🛒 **Cart — {cart.restaurant_name}**", ""]

        for item in cart.items:
            qty = item.get("quantity", 1)
            name = item.get("name", "Unknown")
            price = item.get("price", 0)
            variant = item.get("variant", "")
            line = f"  • {qty}x {name}"
            if variant:
                line += f" ({variant})"
            line += f" — ₹{price * qty:.0f}"
            lines.append(line)

        lines.append("")
        lines.append(f"  Subtotal: ₹{cart.subtotal:.0f}")
        if cart.delivery_fee > 0:
            lines.append(f"  Delivery: ₹{cart.delivery_fee:.0f}")
        lines.append(f"  **Total: ₹{cart.total:.0f}**")

        return "\n".join(lines)
