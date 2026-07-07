from decimal import Decimal
from dataclasses import dataclass

from investing_algorithm_framework.domain.models.order.order_side import OrderSide
from .forex_pair import ForexPair


@dataclass(frozen=True)
class SwapRate:
    pair: ForexPair
    long_rate: Decimal = Decimal("0")
    short_rate: Decimal = Decimal("0")

    def calculate_swap(
        self,
        side: OrderSide,
        units: Decimal,
        days_held: int = 1,
        held_through_wednesday: bool = False,
    ) -> Decimal:
        if days_held == 0:
            return Decimal("0")

        if OrderSide.BUY.equals(side):
            daily_rate = self.long_rate
        else:
            daily_rate = self.short_rate

        total_days = Decimal(str(days_held))

        if held_through_wednesday:
            total_days += Decimal("2")

        lots = units / Decimal("100000")
        swap_cost = daily_rate * lots * total_days
        return swap_cost.quantize(Decimal("0.01"))

    def supports_pair(self, pair: ForexPair) -> bool:
        return self.pair == pair

    def __repr__(self) -> str:
        return (
            f"SwapRate({self.pair.get_symbol()}, "
            f"long={self.long_rate}, short={self.short_rate})"
        )
