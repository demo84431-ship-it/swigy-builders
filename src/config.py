"""
Food DNA Agent — Configuration

Central configuration for MCP endpoints, OAuth, rate limits, and agent behavior.
All secrets use placeholders — replace with real values before deployment.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OAuthConfig:
    """OAuth 2.1 + PKCE configuration for Swiggy MCP authentication."""

    client_id: str = "YOUR_CLIENT_ID"  # Issued by Swiggy Builders Club
    redirect_uri: str = "http://localhost:3000/callback"
    auth_base_url: str = "https://auth.swiggy.com"
    scope: str = "mcp:tools"
    # Token lifetime: 5 days (432,000 seconds). No refresh tokens in v1.0.
    token_lifetime_seconds: int = 432_000


@dataclass(frozen=True)
class MCPServerConfig:
    """MCP server endpoints — one OAuth token works for all three."""

    food_url: str = "https://mcp.swiggy.com/food"
    instamart_url: str = "https://mcp.swiggy.com/im"
    dineout_url: str = "https://mcp.swiggy.com/dineout"


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting to stay under Swiggy's 120 req/min budget per user.

    We target 100 req/min to leave 20% headroom for tracking, cart ops, etc.
    """

    max_requests_per_minute: int = 100
    request_timeout_seconds: int = 30
    # Exponential backoff parameters
    retry_initial_delay_ms: int = 500
    retry_multiplier: int = 2
    retry_max_delay_ms: int = 8_000
    retry_max_attempts: int = 5
    # Tracking poll interval (must be ≥10s per Swiggy docs)
    tracking_poll_interval_seconds: int = 10


@dataclass(frozen=True)
class AgentConfig:
    """Agent behavior tuning — nudge timing, response shaping, cache TTLs."""

    # Nudge suppression
    quiet_hours_start: int = 23  # 11 PM
    quiet_hours_end: int = 8     # 8 AM
    max_nudges_per_day: int = 3
    nudge_suppress_after_rejection_hours: int = 4

    # Response shaping
    voice_max_options: int = 3
    chat_max_options: int = 8

    # Cache TTLs (seconds)
    orders_cache_ttl: int = 300      # 5 min
    search_cache_ttl: int = 600      # 10 min
    nudge_state_ttl: int = 86_400    # 24 hours

    # Cart limits
    food_cart_max_rupees: int = 1_000
    instamart_cart_min_rupees: int = 99


@dataclass
class Config:
    """Top-level configuration container."""

    oauth: OAuthConfig = field(default_factory=OAuthConfig)
    mcp: MCPServerConfig = field(default_factory=MCPServerConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
