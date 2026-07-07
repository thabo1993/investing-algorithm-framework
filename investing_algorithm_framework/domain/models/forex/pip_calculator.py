from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from .forex_pair import ForexPair
from .lot_size import LotSize


class PipCalculator:

    @staticmethod
    def price_to_pips(
        pair: ForexPair, price_from: Decimal, price_to: Decimal
    ) -> Decimal:
        pip_size = PipCalculator._pip_size(pair)
        diff = abs(price_to - price_from)
        return (diff / pip_size).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def pips_to_price(
        pair: ForexPair, current_price: Decimal, pips: Decimal
    ) -> Decimal:
        pip_size = PipCalculator._pip_size(pair)
        return current_price + (pips * pip_size)

    @staticmethod
    def pip_value(
        pair: ForexPair,
        units: Union[int, Decimal, LotSize],
        quote_to_base_rate: Decimal = Decimal("1.0"),
    ) -> Decimal:
        if isinstance(units, LotSize):
            units = units.to_decimal()
        else:
            units = Decimal(str(units))
        pip_size = PipCalculator._pip_size(pair)
        pip_value_in_quote = pip_size * units
        return pip_value_in_quote * quote_to_base_rate

    @staticmethod
    def format_price(pair: ForexPair, price: Decimal) -> str:
        fmt = f"0:.{pair.display_decimal_places}f"
        # Manually format to correct decimal places
        quantizer = Decimal("0." + "0" * pair.display_decimal_places)
        rounded = price.quantize(quantizer, rounding=ROUND_HALF_UP)
        return str(rounded)

    @staticmethod
    def _pip_size(pair: ForexPair) -> Decimal:
        return Decimal(f"0.{'0' * (pair.pip_decimal_places - 1)}1")

    @staticmethod
    def calculate_pnl(
        pair: ForexPair,
        entry_price: Decimal,
        exit_price: Decimal,
        units: Union[int, Decimal, LotSize],
        quote_to_base_rate: Decimal = Decimal("1.0"),
    ) -> dict:
        pips = PipCalculator.price_to_pips(pair, entry_price, exit_price)
        pv = PipCalculator.pip_value(pair, units, quote_to_base_rate)
        pip_pnl = pips * pv / Decimal("1.0")

        return {
            "pips": pips,
            "pip_value": pv,
            "pip_pnl_in_quote": pip_pnl,
            "pip_pnl_in_base": pip_pnl * quote_to_base_rate,
        }
