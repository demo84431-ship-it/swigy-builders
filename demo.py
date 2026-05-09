#!/usr/bin/env python3
"""
FoodDNA Agent — Interactive Demo

Run this script to see the FoodDNA agent in action with simulated MCP data.
Demonstrates 5 key scenarios that showcase psychology-first food intelligence.

Usage:
    python demo.py              # Run all scenarios
    python demo.py --scenario 2 # Run specific scenario
    python demo.py --voice      # Show voice output format
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ── ANSI colors for terminal ────────────────────────────────────────────────

class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


def banner(text: str, color: str = C.CYAN) -> None:
    width = 64
    print(f"\n{color}{'━' * width}")
    print(f"  {text}")
    print(f"{'━' * width}{C.RESET}\n")


def section(title: str) -> None:
    print(f"\n{C.BOLD}{C.BLUE}┌─ {title} {'─' * (58 - len(title))}┐{C.RESET}")


def agent_says(text: str) -> None:
    print(f"{C.GREEN}{C.BOLD}🤖 Agent:{C.RESET} {text}")


def user_says(text: str) -> None:
    print(f"{C.YELLOW}{C.BOLD}👤 User:{C.RESET} {text}")


def thinking(text: str) -> None:
    print(f"{C.DIM}   ⚙ {text}{C.RESET}")


def psychology(text: str) -> None:
    print(f"{C.MAGENTA}   🧠 Psychology: {text}{C.RESET}")


def mcp_call(text: str) -> None:
    print(f"{C.CYAN}   📡 MCP: {text}{C.RESET}")


def divider() -> None:
    print(f"{C.DIM}{'─' * 64}{C.RESET}")


# ── Mock Food DNA Profile ───────────────────────────────────────────────────

@dataclass
class MockFoodDNA:
    """Simulated Food DNA profile for demo purposes."""

    user_id: str = "user_arjun_28"
    name: str = "Arjun"
    age: int = 28
    city: str = "Bengaluru"
    origin: str = "Chennai"

    # Dimension 1: Dietary Identity (non-negotiable)
    dietary_type: str = "vegetarian"
    dietary_strictness: float = 0.85
    home_vs_outside: float = 0.30  # eggetarian outside

    # Dimension 2: Regional Identity
    region: str = "south_indian"
    state: str = "tamil_nadu"
    cuisine_affinity: dict = field(default_factory=lambda: {
        "south_indian": 0.50, "north_indian": 0.18, "chinese": 0.15,
        "italian": 0.08, "street_food": 0.05, "healthy": 0.04,
    })
    rice_vs_wheat: float = 0.85
    spice_tolerance: float = 0.70

    # Dimension 3: Temporal Patterns
    peak_breakfast: int = 8
    peak_lunch: int = 13
    peak_dinner: int = 21
    late_night_ratio: float = 0.12
    weekend_ratio: float = 0.35
    order_interval_days: float = 1.8

    # Dimension 4: Price Psychology
    avg_order_value: float = 280
    price_sensitivity: float = 0.55
    coupon_usage_rate: float = 0.40
    budget_tier: str = "moderate"

    # Dimension 5: Health Orientation
    health_awareness: float = 0.45
    change_stage: str = "contemplation"

    # Dimension 6: Social Dynamics
    solo_ratio: float = 0.70
    couple_ratio: float = 0.15
    family_ratio: float = 0.10
    group_ratio: float = 0.05

    # Dimension 7: Emotional Patterns
    comfort_foods: list = field(default_factory=lambda: ["Curd Rice", "Sambar Rice", "Dal Rice"])
    celebration_foods: list = field(default_factory=lambda: ["Biryani", "Pizza"])
    stress_level: float = 0.25

    # Dimension 8: Life Stage
    life_stage: str = "young_professional_alone"
    cooking_capability: str = "none"
    financial_comfort: str = "comfortable"

    # Dimension 9: Habit Profile
    habit_strength: float = 0.72
    friday_biryani: bool = True
    morning_dosa: bool = True
    recurring_items: list = field(default_factory=lambda: [
        {"item": "Masala Dosa", "orders": 12, "restaurant": "Saravana Bhavan"},
        {"item": "Filter Coffee", "orders": 18, "restaurant": "Saravana Bhavan"},
        {"item": "Biryani", "orders": 8, "restaurant": "Meghana Foods"},
        {"item": "Curd Rice", "orders": 6, "restaurant": "Saravana Bhavan"},
    ])
    recurring_restaurants: list = field(default_factory=lambda: [
        {"name": "Saravana Bhavan", "orders": 18, "cuisine": "south_indian"},
        {"name": "Meghana Foods", "orders": 8, "cuisine": "north_indian"},
        {"name": "Chaat Street", "orders": 5, "cuisine": "street_food"},
    ])

    # Meta
    data_points: int = 67
    confidence_score: float = 0.82


def display_profile(dna: MockFoodDNA) -> None:
    """Display the Food DNA profile beautifully."""

    section("FOOD DNA PROFILE")
    print(f"""
{C.BOLD}👤 {dna.name}{C.RESET}, {dna.age}, {dna.city} (from {dna.origin})
{C.DIM}Data points: {dna.data_points} orders | Confidence: {dna.confidence_score:.0%}{C.RESET}

{C.BOLD}━━━ IDENTITY (Non-negotiable) ━━━{C.RESET}
  🥬 Dietary:     {C.GREEN}{dna.dietary_type}{C.RESET} (strictness: {dna.dietary_strictness:.0%})
  🗺️  Regional:    {dna.region} ({dna.state})
  🍚 Rice/Wheat:  {dna.rice_vs_wheat:.0%} rice-dominant
  🌶️  Spice:       {dna.spice_tolerance:.0%}

{C.BOLD}━━━ BEHAVIORAL (Learned) ━━━{C.RESET}
  🍽️  Top cuisines: {', '.join(f'{k} ({v:.0%})' for k, v in sorted(dna.cuisine_affinity.items(), key=lambda x: -x[1])[:3])}
  💰 Avg order:    ₹{int(dna.avg_order_value)} ({dna.budget_tier})
  🕐 Peak dinner:  {dna.peak_dinner}:00
  📊 Solo/Family:  {dna.solo_ratio:.0%} / {dna.family_ratio:.0%}

{C.BOLD}━━━ HABITS (Very stable, lr=0.05) ━━━{C.RESET}
  💪 Habit strength: {dna.habit_strength:.0%}
  🔄 Friday biryani: {'✅ Yes' if dna.friday_biryani else '❌ No'}
  🌅 Morning dosa:   {'✅ Yes' if dna.morning_dosa else '❌ No'}
  📋 Top items:      {', '.join(i['item'] for i in dna.recurring_items[:3])}

{C.BOLD}━━━ EMOTIONAL (Fast-changing, lr=0.50) ━━━{C.RESET}
  😌 Comfort foods:  {', '.join(dna.comfort_foods[:3])}
  🎉 Celebration:    {', '.join(dna.celebration_foods[:2])}
  😰 Stress level:   {dna.stress_level:.0%}
""")


# ── Demo Scenarios ──────────────────────────────────────────────────────────

def scenario_1_order_usual(dna: MockFoodDNA, voice: bool = False) -> None:
    """Scenario 1: 'Order my usual' — habit detection."""

    section("SCENARIO 1: \"Order My Usual\"")
    user_says("Order my usual")
    print()

    thinking("Fetching Food DNA profile...")
    time.sleep(0.3)
    mcp_call("get_food_orders → 67 orders in 30 days")
    time.sleep(0.2)
    mcp_call("get_addresses → Koramangala, Bengaluru")
    time.sleep(0.2)

    thinking("Analyzing habit profile...")
    thinking(f"  habit_strength = {dna.habit_strength} (>0.6 → HIGH)")
    thinking(f"  top item = Masala Dosa (12 orders)")
    thinking(f"  top restaurant = Saravana Bhavan (18 orders)")
    thinking(f"  dietary_identity = vegetarian (HARD FILTER)")
    thinking(f"  current_hour = 8:30 AM → breakfast window")
    time.sleep(0.3)

    psychology("Habit Loop (Duhigg): CUE=morning → ROUTINE=masala dosa → REWARD=familiar taste + energy")
    psychology("High habit strength → suggest 'your usual' directly, don't show alternatives")
    print()

    if voice:
        agent_says("Your usual masala dosa from Saravana Bhavan? Want me to order that?")
    else:
        agent_says(f"""
{C.BOLD}🍽️ Your usual{C.RESET}

{C.BOLD}Masala Dosa{C.RESET} from {C.BOLD}Saravana Bhavan{C.RESET}
Based on your ordering pattern — you love this! 12 orders in the past month.
{C.DIM}Vegetarian · ₹85 · 15-20 min{C.RESET}

Shall I add it to your cart?""")


def scenario_2_friday_biryani(dna: MockFoodDNA, voice: bool = False) -> None:
    """Scenario 2: 'It's Friday' — proactive biryani suggestion."""

    section("SCENARIO 2: \"It's Friday\" (Proactive)")
    user_says("It's Friday")
    print()

    thinking("Checking day-of-week pattern...")
    time.sleep(0.3)
    mcp_call("get_food_orders → day_distribution[Friday] = 0.22 (>0.15 threshold)")
    time.sleep(0.2)

    thinking("Detecting temporal habits...")
    thinking(f"  temporal_habits: 'friday' → strength 0.80")
    thinking(f"  recurring_items: 'Biryani' → 8 orders")
    thinking(f"  cuisine_affinity: north_indian = 0.18")
    thinking(f"  current_hour = 19:00 (>17:00 → biryani time)")
    time.sleep(0.3)

    psychology("Habit Loop: CUE=Friday evening → ROUTINE=biryani → REWARD=weekend celebration")
    psychology("Cultural psychology: Friday biryani is a reinforced Indian food ritual")
    psychology("This is NOT random — it's a culturally embedded habit loop")
    print()

    if voice:
        agent_says("Friday vibes! Your usual biryani from Meghana Foods? Want me to order?")
    else:
        agent_says(f"""
{C.BOLD}🎉 It's Friday!{C.RESET}

Your usual {C.BOLD}biryani{C.RESET} — because Friday deserves a celebration.
This is your weekend reward ritual — 4 consecutive Fridays of biryani!

{C.DIM}North Indian · ₹280 · Meghana Foods · 30-40 min{C.RESET}

Shall I order from Meghana Foods?""")


def scenario_3_plan_evening(dna: MockFoodDNA, voice: bool = False) -> None:
    """Scenario 3: 'Plan my evening' — cross-server fusion."""

    section("SCENARIO 3: \"Plan My Evening\" (Cross-Server)")
    user_says("Plan my evening")
    print()

    thinking("Cross-server intelligence — combining all 3 MCP servers...")
    time.sleep(0.3)
    mcp_call("Dineout: search_restaurants_dineout('dinner') → Barbeque Nation 4.5⭐")
    time.sleep(0.2)
    mcp_call("Dineout: get_available_slots → 7:30 PM available")
    time.sleep(0.2)
    mcp_call("Food: get_food_orders → top restaurant: Meghana Foods")
    time.sleep(0.2)
    mcp_call("Social dynamics: family_ratio = 0.65 → family dining preferred")
    time.sleep(0.3)

    psychology("Cross-server fusion: Food + Dineout signals combined")
    psychology("Social dynamics profiling: family context detected")
    psychology("Presenting both options — user maintains autonomy (SDT)")
    print()

    if voice:
        agent_says("Dinner out at Barbeque Nation at 7:30? Or order in from Meghana Foods?")
    else:
        agent_says(f"""
{C.BOLD}🌙 Your evening plan:{C.RESET}

{C.BOLD}Option 1: Dine out{C.RESET}
🍽️ {C.BOLD}Barbeque Nation{C.RESET} — 4.5⭐
   Table for 4 available at 7:30 PM
   Family dinner buffet — ₹799 per person

{C.BOLD}Option 2: Order in{C.RESET}
🍕 {C.BOLD}Meghana Foods{C.RESET} — Your usual biryani
   Delivered by 8:15 PM · ₹280

Which sounds better for tonight?""")


def scenario_4_restaurant_closed(dna: MockFoodDNA, voice: bool = False) -> None:
    """Scenario 4: Restaurant closed — error recovery."""

    section("SCENARIO 4: Restaurant Closed (Error Recovery)")
    user_says("Order from Paradise Biryani")
    print()

    thinking("Searching for Paradise Biryani...")
    time.sleep(0.3)
    mcp_call("search_restaurants('Paradise Biryani') → availabilityStatus: CLOSED ❌")
    time.sleep(0.2)

    thinking("Error recovery triggered — finding psychologically similar alternatives...")
    thinking("  Closed restaurant: cuisine=north_indian, item=biryani")
    thinking("  Food DNA scoring: regional_affinity=0.18, habit_match=biryani")
    time.sleep(0.3)
    mcp_call("search_restaurants('biryani', open_only=True) → 3 matches")
    time.sleep(0.2)

    psychology("Error recovery with intelligence — not random alternatives")
    psychology("Scoring: same cuisine + comparable price + familiar comfort")
    psychology("Food DNA weighted: regional(0.20) + habit(0.15) + price(0.10)")
    print()

    if voice:
        agent_says("Paradise Biryani is closed. How about Meghana Foods biryani? Similar style, ₹280.")
    else:
        agent_says(f"""
{C.BOLD}😔 Paradise Biryani is closed right now.{C.RESET}

But here are similar options based on your taste:

{C.BOLD}1. Meghana Foods{C.RESET} — Biryani, ₹280 · 30-40 min
   {C.DIM}Similar to Paradise — same Hyderabadi style{C.RESET}

{C.BOLD}2. Biryani By Kilo{C.RESET} — Biryani, ₹320 · 35-45 min
   {C.DIM}Dum biryani, sealed handi — premium experience{C.RESET}

{C.BOLD}3. Behrouz Biryani{C.RESET} — Biryani, ₹250 · 25-35 min
   {C.DIM}Lucknowi style — different but delicious{C.RESET}

Want me to order from one of these?""")


def scenario_5_festival(dna: MockFoodDNA, voice: bool = False) -> None:
    """Scenario 5: Festival awareness — Diwali."""

    section("SCENARIO 5: \"Diwali Tomorrow\" (Festival Awareness)")
    user_says("Diwali is tomorrow")
    print()

    thinking("Checking festival calendar...")
    time.sleep(0.3)
    mcp_call("FESTIVAL_CALENDAR['diwali'] → foods: [mithai, namkeen, dry_fruits]")
    time.sleep(0.2)

    thinking("Applying filters...")
    thinking(f"  Dietary identity: {dna.dietary_type} → all festival foods COMPLIANT ✅")
    thinking(f"  Regional identity: {dna.region} → South Indian sweets preferred")
    thinking(f"  Price sensitivity: DROP by 0.3 (festival spending tolerance)")
    thinking(f"  Social context: family_ratio = 0.65 → family celebration")
    time.sleep(0.3)

    mcp_call("search_restaurants('mithai') → Sri Krishna Sweets, Haldiram's")
    time.sleep(0.2)
    mcp_call("search_products('dry fruits') → Instamart options")
    time.sleep(0.2)

    psychology("Cultural psychology: Diwali = mithai (non-negotiable cultural expression)")
    psychology("Regional identity filter: South Indian → Mysore Pak > Kaju Katli")
    psychology("Price anchoring: festival budget is separate from daily budget")
    print()

    if voice:
        agent_says("Diwali vibes! How about traditional mithai from Sri Krishna Sweets?")
    else:
        agent_says(f"""
{C.BOLD}🪔 Diwali Special!{C.RESET}

Traditional {C.BOLD}Mithai{C.RESET}, {C.BOLD}Namkeen{C.RESET}, and {C.BOLD}Dry Fruits{C.RESET} — perfect for the celebration.

Based on your South Indian background:
🍬 {C.BOLD}Mysore Pak{C.RESET} from Sri Krishna Sweets — ₹350
🍬 {C.BOLD}Kaju Katli{C.RESET} from Haldiram's — ₹280
🥜 {C.BOLD}Dry Fruit Mix{C.RESET} from Instamart — ₹180

{C.DIM}Festival price sensitivity: reduced (celebration budget){C.RESET}

Shall I order sweets for the family?""")


# ── Main ────────────────────────────────────────────────────────────────────

def run_all_scenarios(voice: bool = False) -> None:
    """Run all 5 demo scenarios."""

    dna = MockFoodDNA()

    banner("FoodDNA Agent — Psychology-First Food Intelligence", C.CYAN)
    print(f"{C.DIM}Built for Swiggy Builders Club | Psychology Master's graduate{C.RESET}")
    print(f"{C.DIM}Cross-server behavioral fusion: Food + Instamart + Dineout{C.RESET}")
    print(f"{C.DIM}10 psychological dimensions | 6 behavioral frameworks{C.RESET}")

    display_profile(dna)

    divider()
    input(f"{C.DIM}Press Enter to start demo scenarios...{C.RESET}")

    scenarios = [
        ("Order My Usual", scenario_1_order_usual),
        ("Friday Biryani", scenario_2_friday_biryani),
        ("Plan My Evening", scenario_3_plan_evening),
        ("Restaurant Closed", scenario_4_restaurant_closed),
        ("Diwali Festival", scenario_5_festival),
    ]

    for i, (name, fn) in enumerate(scenarios, 1):
        fn(dna, voice=voice)
        if i < len(scenarios):
            print()
            input(f"{C.DIM}Press Enter for next scenario ({i+1}/5)...{C.RESET}")

    banner("Demo Complete", C.GREEN)
    print(f"""
{C.BOLD}What you just saw:{C.RESET}

  1. {C.GREEN}Habit detection{C.RESET} — The agent knows your usual, not just your last order
  2. {C.GREEN}Proactive intelligence{C.RESET} — Suggests food BEFORE you ask (Friday biryani)
  3. {C.GREEN}Cross-server fusion{C.RESET} — Combines Food + Dineout for evening planning
  4. {C.GREEN}Error recovery{C.RESET} — Finds psychologically similar alternatives, not random ones
  5. {C.GREEN}Festival awareness{C.RESET} — Understands cultural food associations

{C.BOLD}The difference:{C.RESET}
  Other agents show you restaurants. FoodDNA understands {C.MAGENTA}why{C.RESET} you eat.

{C.DIM}Built on: Habit Loop Theory, Self-Determination Theory, Nudge Theory,
Transtheoretical Model, Behavioral Economics, Cultural Psychology{C.RESET}
""")


def main() -> None:
    voice = "--voice" in sys.argv
    scenario = None
    for arg in sys.argv[1:]:
        if arg.startswith("--scenario"):
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                scenario = int(sys.argv[idx + 1])

    dna = MockFoodDNA()

    if scenario:
        banner(f"FoodDNA Agent — Scenario {scenario}", C.CYAN)
        display_profile(dna)
        fns = {
            1: scenario_1_order_usual,
            2: scenario_2_friday_biryani,
            3: scenario_3_plan_evening,
            4: scenario_4_restaurant_closed,
            5: scenario_5_festival,
        }
        if scenario in fns:
            fns[scenario](dna, voice=voice)
        else:
            print(f"Unknown scenario: {scenario}. Use 1-5.")
    else:
        run_all_scenarios(voice=voice)


if __name__ == "__main__":
    main()
