"""
Food DNA Agent — MCP Client

Wraps communication with Swiggy's three MCP servers (Food, Instamart, Dineout).
Handles OAuth 2.1 + PKCE authentication, retry logic, error classification,
rate limiting, and session management.

All three servers share a single OAuth access token (JWT, Bearer type).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .config import Config, RateLimitConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

class ErrorBucket(Enum):
    """Classification of MCP error responses.

    Determines whether to retry, re-auth, or surface to the user.
    Based on Swiggy MCP error-handling docs (05-error-handling.md).
    """
    AUTH = "auth"              # 401 / -32001 → re-run OAuth
    BAD_INPUT = "bad_input"    # 400 → fix args, don't retry
    UPSTREAM_TIMEOUT = "upstream_timeout"  # 504 → backoff + retry
    UPSTREAM_ERROR = "upstream_error"      # 502/503 → backoff + retry
    DOMAIN = "domain"          # 200 + success:false → surface, don't retry
    INTERNAL = "internal"      # 500 / -32603 → backoff once, report if persists
    NETWORK = "network"        # timeout / connection error → retry
    UNKNOWN = "unknown"


@dataclass
class MCPError(Exception):
    """Structured MCP error with classification."""

    bucket: ErrorBucket
    message: str
    status_code: int = 0
    rpc_code: int = 0
    report_link: Optional[str] = None
    report_hint: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.bucket.value}] {self.message}"


# ---------------------------------------------------------------------------
# Rate limiter (sliding window, per-user)
# ---------------------------------------------------------------------------

class RateLimiter:
    """Sliding-window rate limiter targeting 100 req/min (20% headroom)."""

    def __init__(self, max_per_minute: int = 100) -> None:
        self.max_per_minute = max_per_minute
        self._timestamps: list[float] = []

    def _prune(self) -> None:
        cutoff = time.time() - 60.0
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def can_call(self) -> bool:
        self._prune()
        return len(self._timestamps) < self.max_per_minute

    def record(self) -> None:
        self._timestamps.append(time.time())

    async def wait_for_slot(self) -> None:
        """Block until a rate-limit slot is available."""
        while not self.can_call():
            await asyncio.sleep(0.1)
        self.record()


# ---------------------------------------------------------------------------
# OAuth 2.1 + PKCE helpers
# ---------------------------------------------------------------------------

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256).

    Returns:
        (code_verifier, code_challenge) — both base64url-encoded, no padding.
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    state: str,
    scope: str = "mcp:tools",
    auth_base: str = "https://auth.swiggy.com",
) -> str:
    """Build the OAuth authorization URL for browser redirect."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "scope": scope,
    }
    return f"{auth_base}/auth/authorize?{urlencode(params)}"


async def exchange_code_for_token(
    auth_base_url: str,
    code: str,
    code_verifier: str,
    client_id: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Exchange authorization code for access token.

    Returns the token response dict: access_token, token_type, expires_in, scope.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{auth_base_url}/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Token store (in-memory; swap for Redis/DB in production)
# ---------------------------------------------------------------------------

@dataclass
class TokenStore:
    """Manages the OAuth access token lifecycle."""

    access_token: Optional[str] = None
    expires_at: float = 0.0  # epoch seconds

    @property
    def is_valid(self) -> bool:
        return self.access_token is not None and time.time() < self.expires_at - 60

    def set_token(self, token: str, expires_in: int) -> None:
        self.access_token = token
        self.expires_at = time.time() + expires_in

    def clear(self) -> None:
        self.access_token = None
        self.expires_at = 0.0


# ---------------------------------------------------------------------------
# MCP Client
# ---------------------------------------------------------------------------

class MCPClient:
    """Async client for Swiggy MCP servers.

    Usage:
        client = MCPClient(config)
        await client.authenticate(authorization_code, code_verifier)
        result = await client.call_tool("food", "get_addresses")
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._token = TokenStore()
        self._rate_limiter = RateLimiter(config.rate_limit.max_requests_per_minute)
        self._http: Optional[httpx.AsyncClient] = None

    # -- lifecycle -----------------------------------------------------------

    async def __aenter__(self) -> "MCPClient":
        self._http = httpx.AsyncClient(timeout=self._config.rate_limit.request_timeout_seconds)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._http:
            await self._http.aclose()

    # -- authentication ------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        return self._token.is_valid

    async def authenticate(self, auth_code: str, code_verifier: str) -> dict[str, Any]:
        """Exchange an authorization code for an access token.

        Call this after the user completes the browser-based OAuth flow.
        """
        token_data = await exchange_code_for_token(
            auth_base_url=self._config.oauth.auth_base_url,
            code=auth_code,
            code_verifier=code_verifier,
            client_id=self._config.oauth.client_id,
            redirect_uri=self._config.oauth.redirect_uri,
        )
        self._token.set_token(token_data["access_token"], token_data["expires_in"])
        logger.info("OAuth token acquired, expires in %ds", token_data["expires_in"])
        return token_data

    def set_access_token(self, token: str, expires_in: int = 432_000) -> None:
        """Manually set an access token (e.g., loaded from persistent storage)."""
        self._token.set_token(token, expires_in)

    def get_auth_url(self) -> tuple[str, str, str]:
        """Generate OAuth authorization URL and PKCE parameters.

        Returns:
            (authorize_url, code_verifier, state) — store verifier+state for callback.
        """
        verifier, challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(16)
        url = build_authorize_url(
            client_id=self._config.oauth.client_id,
            redirect_uri=self._config.oauth.redirect_uri,
            code_challenge=challenge,
            state=state,
            scope=self._config.oauth.scope,
            auth_base=self._config.oauth.auth_base_url,
        )
        return url, verifier, state

    # -- tool calls ----------------------------------------------------------

    def _server_url(self, server: str) -> str:
        urls = {
            "food": self._config.mcp.food_url,
            "instamart": self._config.mcp.instamart_url,
            "dineout": self._config.mcp.dineout_url,
        }
        if server not in urls:
            raise ValueError(f"Unknown server: {server}. Must be one of {list(urls.keys())}")
        return urls[server]

    def _classify_error(self, status_code: int, data: dict[str, Any]) -> ErrorBucket:
        """Classify an MCP error response into a bucket."""
        rpc_code = data.get("error", {}).get("code", 0) if isinstance(data.get("error"), dict) else 0

        if status_code == 401 or rpc_code == -32001:
            return ErrorBucket.AUTH
        if status_code == 400:
            return ErrorBucket.BAD_INPUT
        if status_code == 504:
            return ErrorBucket.UPSTREAM_TIMEOUT
        if status_code in (502, 503):
            return ErrorBucket.UPSTREAM_ERROR
        if status_code == 500 or rpc_code == -32603:
            return ErrorBucket.INTERNAL
        if status_code == 200 and data.get("success") is False:
            return ErrorBucket.DOMAIN
        return ErrorBucket.UNKNOWN

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Optional[dict[str, Any]] = None,
        request_id: int = 1,
        _is_order_placement: bool = False,
    ) -> dict[str, Any]:
        """Call an MCP tool with retry logic and error classification.

        Args:
            server: "food", "instamart", or "dineout"
            tool_name: The MCP tool name (e.g., "get_addresses")
            arguments: Tool arguments dict
            request_id: JSON-RPC request ID
            _is_order_placement: Internal flag — if True, uses check-then-retry
                for 5xx errors (place_food_order / checkout / book_table are NOT idempotent).

        Returns:
            Parsed JSON response from the MCP server.

        Raises:
            MCPError: Classified error that the caller can handle.
        """
        if not self._token.is_valid:
            raise MCPError(ErrorBucket.AUTH, "No valid access token. Run OAuth flow first.")

        url = self._server_url(server)
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
            "id": request_id,
        }
        headers = {
            "Authorization": f"Bearer {self._token.access_token}",
            "Content-Type": "application/json",
        }

        delay = self._config.rate_limit.retry_initial_delay_ms / 1000.0
        max_retries = self._config.rate_limit.retry_max_attempts

        for attempt in range(max_retries + 1):
            await self._rate_limiter.wait_for_slot()

            try:
                assert self._http is not None, "Client not initialized. Use 'async with MCPClient(...)'"
                resp = await self._http.post(url, json=payload, headers=headers)
            except httpx.TimeoutException:
                if attempt < max_retries:
                    logger.warning("Timeout on %s/%s attempt %d, retrying…", server, tool_name, attempt + 1)
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self._config.rate_limit.retry_max_delay_ms / 1000.0)
                    continue
                raise MCPError(ErrorBucket.NETWORK, f"Timeout after {max_retries} retries: {server}/{tool_name}")

            # Success path
            if resp.status_code == 200:
                data = resp.json()
                # Domain failure (success: false) — don't retry
                if data.get("success") is False:
                    error = data.get("error", {})
                    raise MCPError(
                        ErrorBucket.DOMAIN,
                        error.get("message", "Domain failure"),
                        report_link=error.get("reportLink"),
                        report_hint=error.get("reportHint"),
                    )
                return data

            # Classify the error
            try:
                data = resp.json()
            except Exception:
                data = {}

            bucket = self._classify_error(resp.status_code, data)
            error_msg = data.get("error", {}).get("message", resp.text) if isinstance(data.get("error"), dict) else resp.text

            # Auth — re-raise immediately, caller must re-auth
            if bucket == ErrorBucket.AUTH:
                self._token.clear()
                raise MCPError(bucket, f"Auth failure: {error_msg}", status_code=resp.status_code)

            # Bad input — don't retry
            if bucket == ErrorBucket.BAD_INPUT:
                raise MCPError(bucket, f"Bad input: {error_msg}", status_code=resp.status_code)

            # Domain failure (already handled above, but defensive)
            if bucket == ErrorBucket.DOMAIN:
                raise MCPError(bucket, error_msg, status_code=resp.status_code)

            # Order placement: check-then-retry for 5xx
            if _is_order_placement and resp.status_code >= 500:
                if attempt == 0:
                    logger.warning("5xx on %s/%s — checking if order went through…", server, tool_name)
                    await asyncio.sleep(2)
                    # Check if order was placed despite the error
                    check_tool = {"food": "get_food_orders", "instamart": "get_orders", "dineout": "get_booking_status"}
                    try:
                        orders = await self.call_tool(server, check_tool[server])
                        logger.info("Order check result: %s", orders)
                        return orders  # Assume order went through
                    except MCPError:
                        pass  # Safe to retry
                    continue

            # Retryable: upstream timeout/error, internal
            if bucket in (ErrorBucket.UPSTREAM_TIMEOUT, ErrorBucket.UPSTREAM_ERROR, ErrorBucket.INTERNAL, ErrorBucket.NETWORK):
                if attempt < max_retries:
                    logger.warning(
                        "%s on %s/%s attempt %d, retrying in %.1fs…",
                        bucket.value, server, tool_name, attempt + 1, delay,
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self._config.rate_limit.retry_max_delay_ms / 1000.0)
                    continue

            # Max retries exceeded or non-retryable
            raise MCPError(
                bucket,
                f"{bucket.value}: {error_msg}",
                status_code=resp.status_code,
                report_link=data.get("error", {}).get("reportLink") if isinstance(data.get("error"), dict) else None,
            )

        raise MCPError(ErrorBucket.UNKNOWN, f"Exhausted retries for {server}/{tool_name}")

    # -- convenience wrappers ------------------------------------------------

    async def food(self, tool: str, args: Optional[dict] = None) -> dict[str, Any]:
        """Call a Food server tool."""
        return await self.call_tool("food", tool, args)

    async def instamart(self, tool: str, args: Optional[dict] = None) -> dict[str, Any]:
        """Call an Instamart server tool."""
        return await self.call_tool("instamart", tool, args)

    async def dineout(self, tool: str, args: Optional[dict] = None) -> dict[str, Any]:
        """Call a Dineout server tool."""
        return await self.call_tool("dineout", tool, args)

    async def report_error(self, server: str, error_context: str, tool_name: str = "") -> dict[str, Any]:
        """Report an error to Swiggy MCP team."""
        return await self.call_tool(server, "report_error", {
            "errorContext": error_context,
            "toolName": tool_name,
        })
