import os
from dotenv import load_dotenv

load_dotenv()


class ProviderConfig:
    """Configuration for provider rate limiting and retry behavior"""

    RATE_LIMIT_RPS: float = float(os.getenv("RATE_LIMIT_RPS", "0.25"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "5"))

    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    BACKOFF_BASE_SECONDS: float = float(os.getenv("BACKOFF_BASE_SECONDS", "1.0"))
    BACKOFF_MAX_SECONDS: float = float(os.getenv("BACKOFF_MAX_SECONDS", "30.0"))
    JITTER_ENABLED: bool = os.getenv("JITTER_ENABLED", "true").lower() == "true"

    PROVIDER: str = os.getenv("PROVIDER", "openliga").lower()

    OPENLIGA_BASE_URL: str = os.getenv("OPENLIGA_BASE_URL", "https://api.openligadb.de")
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
