from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from .forex_pair import ForexPair


@dataclass(frozen=True)
class MarginRequirement:
    pair: ForexPair
    leverage: int = 30

    @property
    def margin_rate(self) -> Decimal:
        if self.leverage <= 0:
            raise ValueError("Leverage must be positive")
        return Decimal("1") / Decimal(str(self.leverage))

    def required_margin(self, notional: Decimal) -> Decimal:
        return (notional * self.margin_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def supports_pair(self, pair: ForexPair) -> bool:
        return self.pair == pair

    def __repr__(self) -> str:
        return (
            f"MarginRequirement({self.pair.get_symbol()}, "
            f"1:{self.leverage})"
        )
