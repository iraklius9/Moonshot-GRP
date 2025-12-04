import asyncio
import random
import time
from typing import List, Dict, Any
import httpx
from .base import SportsProvider
from .config import ProviderConfig


class TokenBucket:
    """Simple token bucket rate limiter"""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst  # max tokens
        self.tokens = burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, blocking if necessary"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.time()


class OpenLigaProvider(SportsProvider):
    """OpenLiga API adapter with rate limiting and exponential backoff"""

    def __init__(self, config: ProviderConfig = None):
        self.config = config or ProviderConfig()
        self.rate_limiter = TokenBucket(self.config.RATE_LIMIT_RPS, self.config.RATE_LIMIT_BURST)
        self.client = httpx.AsyncClient(
            base_url=self.config.OPENLIGA_BASE_URL,
            timeout=self.config.REQUEST_TIMEOUT_SECONDS,
            headers={
                "Accept": "application/json",
                "User-Agent": "ReverseProxyService/1.0",
                "Accept-Encoding": "gzip, deflate, br"
            },
            follow_redirects=True
        )

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional jitter"""
        base_delay = self.config.BACKOFF_BASE_SECONDS * (2 ** attempt)
        if self.config.JITTER_ENABLED:
            jitter = random.uniform(0, base_delay * 0.1)
            delay = min(base_delay + jitter, self.config.BACKOFF_MAX_SECONDS)
        else:
            delay = min(base_delay, self.config.BACKOFF_MAX_SECONDS)
        return delay

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with exponential backoff retry logic"""
        last_exception = None

        for attempt in range(self.config.MAX_RETRIES + 1):
            await self.rate_limiter.acquire()

            try:
                response = await self.client.request(method, url, **kwargs)

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" in content_type and response.status_code == 200:
                    raise ValueError(
                        f"API returned HTML instead of JSON. "
                        f"Status: {response.status_code}, "
                        f"Content-Type: {content_type}, "
                        f"URL: {self.config.OPENLIGA_BASE_URL}{url}, "
                        f"Response preview: {response.text[:300]}"
                    )

                if response.status_code < 500 and response.status_code != 429:
                    return response

                if attempt < self.config.MAX_RETRIES:
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

                return response

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                if attempt < self.config.MAX_RETRIES:
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise

        if last_exception:
            raise last_exception
        return response

    async def list_leagues(self) -> List[Dict[str, Any]]:
        """List all available leagues"""
        response = await self._request_with_retry("GET", "/getavailableleagues")
        response.raise_for_status()
        content = response.text
        if not content.strip():
            raise ValueError("Empty response from API")
        try:
            return response.json()
        except Exception as e:
            raise ValueError(
                f"Failed to parse JSON response. Status: {response.status_code}, "
                f"Content-Type: {response.headers.get('content-type')}, "
                f"Body length: {len(content)}, "
                f"Body preview: {content[:200]}"
            ) from e

    async def get_league_matches(self, league_id: str) -> List[Dict[str, Any]]:
        """Get matches for a specific league"""
        response = await self._request_with_retry("GET", f"/getmatchdata/{league_id}")
        response.raise_for_status()
        content = response.text
        if not content.strip():
            raise ValueError("Empty response from API")
        try:
            return response.json()
        except Exception as e:
            raise ValueError(
                f"Failed to parse JSON response. Status: {response.status_code}, "
                f"Content-Type: {response.headers.get('content-type')}, "
                f"Body length: {len(content)}, "
                f"Body preview: {content[:200]}"
            ) from e

    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """
        Get team information by ID

        Note: OpenLiga API doesn't have a direct endpoint for team by ID.
        This implementation searches through league matches to find the team.
        """
        common_leagues = ["bl1", "bl2", "pl", "sa", "ll"]

        for league_id in common_leagues:
            try:
                matches = await self.get_league_matches(league_id)
                for match in matches:
                    if str(match.get("team1", {}).get("teamId")) == str(team_id):
                        return match.get("team1", {})
                    if str(match.get("team2", {}).get("teamId")) == str(team_id):
                        return match.get("team2", {})
            except Exception:
                continue

        raise ValueError(
            f"Team {team_id} not found. OpenLiga API requires searching through league matches. "
            f"Consider using get_league_matches with a specific leagueId and extracting team information from matches."
        )

    async def get_match(self, match_id: str) -> Dict[str, Any]:
        """
        Get match information by ID

        Note: OpenLiga API doesn't have a direct endpoint for match by ID.
        This implementation searches through league matches to find the match.
        """
        try:
            matches = await self.get_league_matches("bl1")
            for match in matches:
                if str(match.get("matchID")) == str(match_id):
                    return match
            raise ValueError(f"Match {match_id} not found in default league")
        except Exception as e:
            raise ValueError(
                f"Match {match_id} not found. OpenLiga API requires leagueId to search matches. "
                f"Consider using get_league_matches with a specific leagueId and filtering."
            ) from e

    async def close(self):
        await self.client.aclose()
