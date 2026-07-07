import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timezone, timedelta
from decimal import Decimal
from typing import Dict, Optional, Union

from investing_algorithm_framework.domain.models.forex import (
    ForexPair,
    SwapRate,
)
from investing_algorithm_framework.domain.models.order.order_side import (
    OrderSide,
)

logger = logging.getLogger("investing_algorithm_framework")

DEFAULT_ROLLOVER_TIME = time(22, 0, 0, tzinfo=timezone.utc)


@dataclass
class SwapTracker:
    pairs: Dict[str, SwapRate] = field(default_factory=dict)
    rollover_time: time = DEFAULT_ROLLOVER_TIME

    def configure(self, pair: ForexPair, swap_rate: SwapRate):
        self.pairs[pair.get_symbol()] = swap_rate

    def get_swap_rate(self, symbol: str) -> Optional[SwapRate]:
        return self.pairs.get(symbol)

    def _resolve_side(
        self, side: Union[str, OrderSide]
    ) -> OrderSide:
        if isinstance(side, OrderSide):
            return side
        upper = side.upper()
        if upper in ("LONG", "BUY"):
            return OrderSide.BUY
        return OrderSide.SELL

    def calculate_rollover_swap(
        self,
        pair: ForexPair,
        side: Union[str, OrderSide],
        units: Decimal,
        position_held_at_rollover: bool,
    ) -> Decimal:
        if not position_held_at_rollover:
            return Decimal("0")

        swap_rate = self.get_swap_rate(pair.get_symbol())
        if swap_rate is None:
            return Decimal("0")

        return swap_rate.calculate_swap(
            side=self._resolve_side(side),
            units=units,
            days_held=1,
        )

    def calculate_swap_for_date_range(
        self,
        pair: ForexPair,
        side: Union[str, OrderSide],
        units: Decimal,
        entry_date: datetime,
        exit_date: datetime,
    ) -> Decimal:
        swap_rate = self.get_swap_rate(pair.get_symbol())
        if swap_rate is None:
            return Decimal("0")

        order_side = self._resolve_side(side)
        total_swap = Decimal("0")
        current = entry_date.replace(
            hour=self.rollover_time.hour,
            minute=self.rollover_time.minute,
            second=0,
            microsecond=0,
        )

        if current <= entry_date:
            current += timedelta(days=1)

        while current < exit_date:
            weekday = current.weekday()
            if weekday >= 5:
                current += timedelta(days=1)
                continue

            held_through_wednesday = weekday == 2

            days = 3 if held_through_wednesday else 1
            swap = swap_rate.calculate_swap(
                side=order_side,
                units=units,
                days_held=days,
                held_through_wednesday=False,
            )
            total_swap += swap
            current += timedelta(days=1)

        return total_swap.quantize(Decimal("0.01"))
