"""
FoodDNA Agent — Web Server for Railway Deployment

FastAPI app that serves the chat UI and wraps the FoodDNA agent
as a web API. Handles OAuth flow, WebSocket chat, and profile viewing.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import Config, OAuthConfig, MCPServerConfig
from src.agent import FoodDNAAgent
from src.food_dna import FoodDNA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FoodDNA Agent",
    description="Psychology-first AI behavioral intelligence for Swiggy MCP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration from environment ──────────────────────────────────────────

def get_config() -> Config:
    """Build config from environment variables."""
    return Config(
        oauth=OAuthConfig(
            client_id=os.getenv("SWIGGY_CLIENT_ID", "YOUR_CLIENT_ID"),
            redirect_uri=os.getenv("REDIRECT_URI", "http://localhost:3000/api/auth/callback"),
            auth_base_url=os.getenv("AUTH_BASE_URL", "https://auth.swiggy.com"),
        ),
        mcp=MCPServerConfig(
            food_url=os.getenv("MCP_FOOD_URL", "https://mcp.swiggy.com/food"),
            instamart_url=os.getenv("MCP_INSTAMART_URL", "https://mcp.swiggy.com/im"),
            dineout_url=os.getenv("MCP_DINEOUT_URL", "https://mcp.swiggy.com/dineout"),
        ),
    )


# ── Demo mode check ─────────────────────────────────────────────────────────

DEMO_MODE = os.getenv("SWIGGY_CLIENT_ID", "YOUR_CLIENT_ID") == "YOUR_CLIENT_ID"


# ── Profile loading ─────────────────────────────────────────────────────────

PROFILES_DIR = Path(__file__).parent / "profiles"

def load_all_profiles() -> dict[str, dict[str, Any]]:
    """Load all profile JSON files from the profiles directory."""
    profiles = {}
    if not PROFILES_DIR.exists():
        logger.warning("Profiles directory not found: %s", PROFILES_DIR)
        return profiles
    for path in PROFILES_DIR.glob("*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
            profile_id = data.get("id", path.stem)
            profiles[profile_id] = data
            logger.info("Loaded profile: %s (%s)", profile_id, data.get("name", "?"))
        except Exception as e:
            logger.error("Failed to load profile %s: %s", path, e)
    return profiles

ALL_PROFILES = load_all_profiles()

def get_profile_display(profile_id: str) -> dict[str, Any] | None:
    """Get display-safe profile data (no internal fields)."""
    data = ALL_PROFILES.get(profile_id)
    if not data:
        return None
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "age": data.get("age"),
        "city": data.get("city"),
        "origin": data.get("origin"),
        "avatar": data.get("avatar"),
        "tagline": data.get("tagline"),
        "dietary": data.get("dietary_identity", {}).get("primary", "—"),
        "life_stage": data.get("life_stage", {}).get("life_stage", "—"),
        "confidence_score": data.get("confidence_score", 0),
        "data_points": data.get("data_points", 0),
    }


# ── In-memory session store (swap for Redis/DB in production) ───────────────

sessions: dict[str, dict[str, Any]] = {}


def get_session(session_id: str) -> dict[str, Any]:
    if session_id not in sessions:
        sessions[session_id] = {
            "agent": None,
            "access_token": None,
            "code_verifier": None,
            "state": None,
            "dna": None,
            "active_profile": None,  # Profile ID for demo mode
        }
    return sessions[session_id]


# ── Demo mode: profile-aware responses (v2) ──────────────────────────────────────

def get_active_profile_data(session: dict[str, Any]) -> dict[str, Any] | None:
    """Get the full profile data for the session's active profile."""
    profile_id = session.get("active_profile")
    if profile_id and profile_id in ALL_PROFILES:
        return ALL_PROFILES[profile_id]
    # Default to first profile if none selected
    if ALL_PROFILES:
        first_id = next(iter(ALL_PROFILES))
        return ALL_PROFILES[first_id]
    return None


def demo_response(message: str, profile_data: dict[str, Any] | None = None) -> str:
    """Generate demo responses using profile context."""
    msg = message.lower().strip()

    # Extract profile info for personalized responses
    name = "User"
    dietary = "vegetarian"
    city = ""
    comfort_foods = []
    celebration_foods = []
    recurring_items = []
    recurring_restaurants = []
    sample_convs = []
    habits = {}

    if profile_data:
        name = profile_data.get("name", "User")
        dietary = profile_data.get("dietary_identity", {}).get("primary", "vegetarian")
        city = profile_data.get("city", "")
        ep = profile_data.get("emotional_patterns", {})
        comfort_foods = ep.get("comfort_foods", [])
        celebration_foods = ep.get("celebration_foods", [])
        hp = profile_data.get("habit_profile", {})
        recurring_items = hp.get("recurring_items", [])
        recurring_restaurants = hp.get("recurring_restaurants", [])
        habits = hp.get("temporal_habits", [])
        sample_convs = profile_data.get("sample_conversations", [])

    # Top recurring item
    top_item = recurring_items[0] if recurring_items else {"item": "your usual", "orders": 0}
    top_restaurant = recurring_restaurants[0] if recurring_restaurants else {"name": "your usual spot"}

    if any(p in msg for p in ["order my usual", "order something", "i want food"]):
        item = top_item
        rest = top_restaurant
        return (
            f'<div class="rich-card">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🍽️</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">{item.get("item", "Your usual")}</div>'
            f'<div class="rich-card-subtitle">{rest.get("name", "Your usual spot")}</div>'
            f'</div></div>'
            f'<div class="rich-card-meta">'
            f'<span class="meta-chip">⭐ 4.5</span>'
            f'<span class="meta-chip">🕐 15-20 min</span>'
            f'<span class="meta-chip">{dietary.replace("_", " ").title()}</span>'
            f'</div>'
            f'<div class="rich-card-desc">Based on your ordering pattern — {item.get("orders", 0)} orders this month!</div>'
            f'<div class="rich-card-actions">'
            f'<button class="action-btn primary" onclick="sendSuggestion(\'Yes, order it\')">🛒 Order Now</button>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Show me the menu\')">📋 View Menu</button>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Surprise me\')">🎲 Something Else</button>'
            f'</div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    if "friday" in msg:
        friday_habit = next((h for h in habits if h.get("cue") == "friday"), None)
        friday_item = friday_habit.get("routine", "biryani") if friday_habit else "biryani"
        return (
            f'<div class="rich-card">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🎉</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">Friday Special: {friday_item.title()}</div>'
            f'<div class="rich-card-subtitle">{top_restaurant.get("name", "Your usual spot")}</div>'
            f'</div></div>'
            f'<div class="rich-card-meta">'
            f'<span class="meta-chip">⭐ 4.5</span>'
            f'<span class="meta-chip">🕐 30-40 min</span>'
            f'<span class="meta-chip">🔥 Weekend vibes</span>'
            f'</div>'
            f'<div class="rich-card-desc">Your weekend reward ritual — 4 consecutive Fridays!</div>'
            f'<div class="rich-card-actions">'
            f'<button class="action-btn primary" onclick="sendSuggestion(\'Yes, order it\')">🛒 Order Now</button>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Show me the menu\')">📋 View Menu</button>'
            f'</div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    if any(p in msg for p in ["plan my evening", "plan evening", "dinner out"]):
        return (
            f'<div class="rich-card">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🌙</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">Evening Plan for {name}</div>'
            f'<div class="rich-card-subtitle">Cross-server: Food + Dineout</div>'
            f'</div></div>'
            f'<div class="rich-card-options">'
            f'<div class="option-card">'
            f'<div class="option-title">🍽️ Dine Out</div>'
            f'<div class="option-detail">Barbeque Nation — 4.5⭐</div>'
            f'<div class="option-detail">Table at 7:30 PM · Buffet ₹799/person</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Book a table\')">Book Table</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">🍕 Order In</div>'
            f'<div class="option-detail">{top_restaurant.get("name", "Your usual spot")} — Your usual</div>'
            f'<div class="option-detail">Delivered by 8:15 PM</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order in\')">Order In</button>'
            f'</div></div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    if any(p in msg for p in ["healthy", "eat healthy"]):
        return (
            f'<div class="rich-card">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🥗</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">Healthy Picks for {name}</div>'
            f'<div class="rich-card-subtitle">Light but satisfying</div>'
            f'</div></div>'
            f'<div class="rich-card-options">'
            f'<div class="option-card">'
            f'<div class="option-title">Grilled Salad</div>'
            f'<div class="option-detail">₹220 · 25 min · Fresh & protein-rich</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order grilled salad\')">Order</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">Multigrain Dosa</div>'
            f'<div class="option-detail">₹120 · 15 min · Healthier twist on your usual</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order multigrain dosa\')">Order</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">Quinoa Bowl</div>'
            f'<div class="option-detail">₹280 · 30 min · Superfood goodness</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order quinoa bowl\')">Order</button>'
            f'</div></div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    if any(p in msg for p in ["surprise me", "something different", "bored"]):
        return (
            f'<div class="rich-card">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🎲</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">Something Different</div>'
            f'<div class="rich-card-subtitle">Controlled novelty for {name}</div>'
            f'</div></div>'
            f'<div class="rich-card-options">'
            f'<div class="option-card">'
            f'<div class="option-title">Appam & Stew</div>'
            f'<div class="option-detail">₹150 · 20 min · Same comfort, new twist</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order appam\')">Order</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">Indo-Chinese Noodles</div>'
            f'<div class="option-detail">₹180 · 25 min · Fusion adventure</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order noodles\')">Order</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">Thai Green Curry</div>'
            f'<div class="option-detail">₹250 · 30 min · Wild card!</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order thai curry\')">Order</button>'
            f'</div></div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    if any(p in msg for p in ["diwali", "holi", "festival"]):
        return (
            f'<div class="rich-card festival">'
            f'<div class="rich-card-header">'
            f'<div class="rich-card-img">🪔</div>'
            f'<div class="rich-card-info">'
            f'<div class="rich-card-title">Festival Special!</div>'
            f'<div class="rich-card-subtitle">Traditional sweets & treats</div>'
            f'</div></div>'
            f'<div class="rich-card-options">'
            f'<div class="option-card">'
            f'<div class="option-title">🍬 Sweets Combo</div>'
            f'<div class="option-detail">Mysore Pak + Kaju Katli · ₹350</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order sweets\')">Order</button>'
            f'</div>'
            f'<div class="option-card">'
            f'<div class="option-title">🥜 Dry Fruit Mix</div>'
            f'<div class="option-detail">Premium mix from Instamart · ₹180</div>'
            f'<button class="action-btn" onclick="sendSuggestion(\'Order dry fruits\')">Order</button>'
            f'</div></div></div>'
            f'<em>⚡ Demo mode — connect Swiggy to order for real</em>'
        )

    # Fallback: check sample conversations for a match
    for conv in sample_convs:
        if conv.get("user", "").lower().strip() == msg:
            return f"🤖 {conv['agent']}"

    # Default: show help with profile name
    return (
        f'<div class="rich-card">'
        f'<div class="rich-card-header">'
        f'<div class="rich-card-img">🤖</div>'
        f'<div class="rich-card-info">'
        f'<div class="rich-card-title">Hi {name}!</div>'
        f'<div class="rich-card-subtitle">Try one of these</div>'
        f'</div></div>'
        f'<div class="rich-card-options">'
        f'<div class="option-card">'
        f'<div class="option-title">🍕 Order my usual</div>'
        f'<div class="option-detail">Habit detection</div>'
        f'<button class="action-btn" onclick="sendSuggestion(\'Order my usual\')">Try</button>'
        f'</div>'
        f'<div class="option-card">'
        f'<div class="option-title">🎉 It\'s Friday</div>'
        f'<div class="option-detail">Proactive suggestion</div>'
        f'<button class="action-btn" onclick="sendSuggestion(\'It\\\'s Friday\')">Try</button>'
        f'</div>'
        f'<div class="option-card">'
        f'<div class="option-title">🎲 Surprise me</div>'
        f'<div class="option-detail">Controlled novelty</div>'
        f'<button class="action-btn" onclick="sendSuggestion(\'Surprise me\')">Try</button>'
        f'</div></div></div>'
        f'<em>⚡ Demo mode — connect Swiggy for real data</em>'
    )


# ── API Routes ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main page."""
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())


@app.get("/api/health")
async def health():
    return {"status": "ok", "agent": "FoodDNA", "version": "1.0.0", "profiles": len(ALL_PROFILES)}


@app.get("/api/tts")
async def text_to_speech(q: str = "", lang: str = "en"):
    """Proxy Google Translate TTS — free, no API key needed."""
    if not q or len(q) > 500:
        raise HTTPException(400, "Text required (max 500 chars)")

    import httpx
    import urllib.parse

    # Google Translate TTS endpoint
    encoded = urllib.parse.quote(q)
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&idx=0&client=tw-ob&total=1&tl={lang}&q={encoded}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if resp.status_code != 200 or len(resp.content) < 100:
        raise HTTPException(502, "TTS service unavailable")

    return StreamingResponse(
        iter([resp.content]),
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/profiles")
async def list_profiles():
    """List all available demo profiles."""
    profiles = []
    for pid, data in ALL_PROFILES.items():
        profiles.append(get_profile_display(pid))
    return {"profiles": profiles, "count": len(profiles)}


@app.get("/api/profiles/{profile_id}")
async def get_profile_detail(profile_id: str):
    """Get a specific profile's full data."""
    if profile_id not in ALL_PROFILES:
        raise HTTPException(404, f"Profile '{profile_id}' not found")
    return ALL_PROFILES[profile_id]


@app.post("/api/select-profile")
async def select_profile(request: Request):
    """Select a demo profile for the chat session."""
    body = await request.json()
    profile_id = body.get("profile_id", "")
    session_id = body.get("session_id", "default")

    if profile_id not in ALL_PROFILES:
        raise HTTPException(404, f"Profile '{profile_id}' not found")

    session = get_session(session_id)
    session["active_profile"] = profile_id
    profile_data = ALL_PROFILES[profile_id]

    return {
        "status": "ok",
        "profile": get_profile_display(profile_id),
        "dna": profile_data,
    }


@app.get("/api/auth/login")
async def auth_login():
    """Start OAuth flow — returns authorization URL."""
    config = get_config()
    async with FoodDNAAgent(config) as agent:
        url, verifier, state = agent.get_auth_url()

    session_id = state  # Use OAuth state as session ID
    session = get_session(session_id)
    session["code_verifier"] = verifier
    session["state"] = state

    return {
        "auth_url": url,
        "session_id": session_id,
    }


@app.get("/api/auth/callback")
async def auth_callback(code: str, state: str):
    """OAuth callback — exchanges code for token."""
    if DEMO_MODE:
        return RedirectResponse(url="/")

    session = get_session(state)
    if not session.get("code_verifier"):
        raise HTTPException(400, "Invalid session. Please restart login.")

    config = get_config()
    async with FoodDNAAgent(config) as agent:
        token_data = await agent.authenticate(code, session["code_verifier"])
        session["access_token"] = token_data["access_token"]

        # Build profile immediately after auth
        dna = await agent.build_profile()
        session["dna"] = dna.to_dict()

    return RedirectResponse(url="/")


@app.post("/api/chat")
async def chat(request: Request):
    """Handle chat messages. Falls back to demo mode if no credentials."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    session = get_session(session_id)

    # ── Demo mode: use profile-aware responses ────────────────────────
    if DEMO_MODE:
        profile_data = get_active_profile_data(session)
        return {"reply": demo_response(message, profile_data), "mode": "demo"}

    # ── Real mode: use FoodDNA agent with MCP ─────────────────────────
    if not session.get("access_token"):
        return JSONResponse(
            {"error": "Not authenticated. Please login first."},
            status_code=401,
        )

    config = get_config()
    async with FoodDNAAgent(config) as agent:
        agent._mcp.set_access_token(session["access_token"])

        # Load existing profile
        if session.get("dna"):
            agent.dna = FoodDNA.from_dict(session["dna"])

        # Handle intent
        response = await agent.handle_intent(message)

        # Save updated profile
        if agent.dna:
            session["dna"] = agent.dna.to_dict()

    return {"reply": response}


@app.get("/api/profile")
async def get_profile(session_id: str = "default"):
    """Get the current Food DNA profile."""
    session = get_session(session_id)

    if DEMO_MODE:
        profile_data = get_active_profile_data(session)
        if profile_data:
            return profile_data
        return JSONResponse({"error": "No profiles loaded"}, status_code=404)

    if not session.get("dna"):
        return JSONResponse({"error": "No profile. Login first."}, status_code=404)

    return session["dna"]


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    session_id = "default"

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            session_id = data.get("session_id", session_id)

            session = get_session(session_id)

            if DEMO_MODE:
                profile_data = get_active_profile_data(session)
                reply = demo_response(message, profile_data)
                await websocket.send_json({"reply": reply, "mode": "demo"})
                continue

            if not session.get("access_token"):
                await websocket.send_json({"error": "Not authenticated"})
                continue

            config = get_config()
            async with FoodDNAAgent(config) as agent:
                agent._mcp.set_access_token(session["access_token"])
                if session.get("dna"):
                    agent.dna = FoodDNA.from_dict(session["dna"])

                response = await agent.handle_intent(message)

                if agent.dna:
                    session["dna"] = agent.dna.to_dict()

            await websocket.send_json({"reply": response})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


# ── Static files ────────────────────────────────────────────────────────────

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Run (local development) ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
