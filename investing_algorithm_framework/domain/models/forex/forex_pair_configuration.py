from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional

from .forex_pair import ForexPair
from .lot_size import LotSize


@dataclass
class ForexPairConfiguration:
    symbol: str
    swap_long_rate: Optional[Decimal] = None
    swap_short_rate: Optional[Decimal] = None
    margin_leverage: int = 30
    default_lot_size: LotSize = LotSize.MICRO
    pip_decimal_places: Optional[int] = None
    display_decimal_places: Optional[int] = None

    def __post_init__(self):
        self._pair = ForexPair.from_symbol(self.symbol)

    @property
    def pair(self) -> ForexPair:
        return self._pair

    def to_swap_rate(self):
        from .swap_rate import SwapRate

        if self.swap_long_rate is None and self.swap_short_rate is None:
            return None
        return SwapRate(
            pair=self._pair,
            long_rate=self.swap_long_rate or Decimal("0"),
            short_rate=self.swap_short_rate or Decimal("0"),
        )

    def to_margin_requirement(self):
        from .margin_requirement import MarginRequirement

        return MarginRequirement(
            pair=self._pair, leverage=self.margin_leverage
        )
