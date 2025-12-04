from .base import SportsProvider
from .openliga import OpenLigaProvider
from .config import ProviderConfig


def get_provider(config: ProviderConfig = None) -> SportsProvider:
    """
    Factory function to get the configured provider.
    Provider selection is controlled by the PROVIDER environment variable.
    Default: 'openliga'

    To add a new provider:
    1. Create a new provider class inheriting from SportsProvider
    2. Import it here
    3. Add it to the provider_map below
    """
    if config is None:
        config = ProviderConfig()

    provider_map = {
        "openliga": OpenLigaProvider,
    }

    provider_class = provider_map.get(config.PROVIDER)
    if provider_class is None:
        raise ValueError(
            f"Unknown provider: {config.PROVIDER}. "
            f"Available providers: {', '.join(provider_map.keys())}"
        )

    return provider_class(config)


__all__ = ["SportsProvider", "OpenLigaProvider", "ProviderConfig", "get_provider"]
