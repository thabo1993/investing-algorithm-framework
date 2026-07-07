from datetime import datetime
from typing import List, Optional

from investing_algorithm_framework.domain.fx import FXRateProvider


class CrossRateFXRateProvider(FXRateProvider):
    def __init__(self, providers: List[FXRateProvider] = None):
        self._providers = providers or []

    def add_provider(self, provider: FXRateProvider):
        self._providers.append(provider)

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: datetime = None,
    ) -> float:
        from_c = from_currency.upper()
        to_c = to_currency.upper()

        if from_c == to_c:
            return 1.0

        for provider in self._providers:
            if provider.supports_pair(from_c, to_c):
                return provider.get_rate(from_c, to_c, date)

        for provider in self._providers:
            if provider.supports_pair(to_c, from_c):
                rate = provider.get_rate(to_c, from_c, date)
                if rate != 0:
                    return 1.0 / rate

        for provider in self._providers:
            if provider.supports_pair(from_c, "USD"):
                rate_from_usd = provider.get_rate(from_c, "USD", date)
                for provider2 in self._providers:
                    if provider2.supports_pair(to_c, "USD"):
                        rate_to_usd = provider2.get_rate(to_c, "USD", date)
                        if rate_to_usd != 0:
                            return rate_from_usd / rate_to_usd

        raise ValueError(
            f"No FX rate available for {from_c}/{to_c} through any "
            f"registered provider or cross-rate chain."
        )

    def supports_pair(self, from_currency: str, to_currency: str) -> bool:
        from_c = from_currency.upper()
        to_c = to_currency.upper()

        if from_c == to_c:
            return True

        for provider in self._providers:
            if provider.supports_pair(from_c, to_c):
                return True
            if provider.supports_pair(to_c, from_c):
                return True

        has_from_usd = any(
            p.supports_pair(from_c, "USD") for p in self._providers
        )
        has_to_usd = any(
            p.supports_pair(to_c, "USD") for p in self._providers
        )

        return has_from_usd and has_to_usd
