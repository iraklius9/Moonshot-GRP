import pytest
import time
from unittest.mock import patch, MagicMock
import httpx
from app.providers.openliga import OpenLigaProvider, TokenBucket
from app.providers.config import ProviderConfig


class TestTokenBucket:
    """Test token bucket rate limiter"""

    @pytest.mark.asyncio
    async def test_token_bucket_acquire(self):
        """Test acquiring tokens"""
        bucket = TokenBucket(rate=10.0, burst=20)
        start = time.time()
        await bucket.acquire()
        elapsed = time.time() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiting(self):
        """Test rate limiting behavior"""
        bucket = TokenBucket(rate=10.0, burst=2)
        await bucket.acquire()
        await bucket.acquire()

        start = time.time()
        await bucket.acquire()
        elapsed = time.time() - start
        assert 0.05 < elapsed < 0.2


class TestOpenLigaProvider:
    """Test OpenLiga provider"""

    @pytest.fixture
    def config(self):
        """Provider config for testing"""
        config = ProviderConfig()
        config.RATE_LIMIT_RPS = 100
        config.MAX_RETRIES = 2
        config.BACKOFF_BASE_SECONDS = 0.1
        return config

    @pytest.fixture
    def provider(self, config):
        """Create provider instance"""
        return OpenLigaProvider(config)

    @pytest.mark.asyncio
    async def test_list_leagues_success(self, provider):
        """Test successful list_leagues call"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": "1", "name": "League 1"}]
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await provider.list_leagues()
            assert len(result) == 1
            assert result[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_get_league_matches_success(self, provider):
        """Test successful get_league_matches call"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": "m1"}]
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await provider.get_league_matches("bl1")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_retry_on_429(self, provider):
        """Test retry on 429 status code"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429

            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = [{"id": "1"}]
            mock_response_200.raise_for_status = MagicMock()

            mock_request.side_effect = [mock_response_429, mock_response_200]

            result = await provider.list_leagues()
            assert len(result) == 1
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_5xx(self, provider):
        """Test retry on 5xx status code"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_response_500 = MagicMock()
            mock_response_500.status_code = 500

            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = [{"id": "1"}]
            mock_response_200.raise_for_status = MagicMock()

            mock_request.side_effect = [mock_response_500, mock_response_200]

            result = await provider.list_leagues()
            assert len(result) == 1
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, provider):
        """Test retry on timeout"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_request.side_effect = [
                httpx.TimeoutException("Timeout"),
                MagicMock(status_code=200, json=lambda: [{"id": "1"}], raise_for_status=MagicMock())
            ]

            result = await provider.list_leagues()
            assert len(result) == 1
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, provider):
        """Test that max retries are respected"""
        with patch.object(provider.client, 'request') as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_request.return_value = mock_response

            result = await provider._request_with_retry("GET", "/test")
            assert mock_request.call_count == provider.config.MAX_RETRIES + 1
            assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_close_provider(self, provider):
        """Test closing provider"""
        await provider.close()
