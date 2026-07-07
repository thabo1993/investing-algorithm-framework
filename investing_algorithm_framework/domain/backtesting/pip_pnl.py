from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from investing_algorithm_framework.domain.models.forex import (
    ForexPair,
    LotSize,
    PipCalculator,
)


@dataclass(frozen=True)
class PipPnLResult:
    pips: Decimal
    pip_value_in_quote: Decimal
    base_currency_pnl: Decimal


def _pip_size(pair: ForexPair) -> Decimal:
    return Decimal(
        f"0.{'0' * (pair.pip_decimal_places - 1)}1"
    )


def calculate_pip_pnl(
    entry_price: Decimal,
    exit_price: Decimal,
    pair: ForexPair,
    units: Union[int, Decimal, LotSize],
    quote_to_base_rate: Decimal = Decimal("1.0"),
) -> PipPnLResult:
    size = _pip_size(pair)
    diff = exit_price - entry_price
    pips = (diff / size).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    pip_value = PipCalculator.pip_value(
        pair, units, quote_to_base_rate
    )
    base_pnl = (pips * pip_value).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return PipPnLResult(
        pips=pips,
        pip_value_in_quote=pip_value,
        base_currency_pnl=base_pnl,
    )
