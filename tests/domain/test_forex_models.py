import unittest
from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import FrozenInstanceError

from investing_algorithm_framework.domain.models.forex import (
    ForexPair,
    LotSize,
    PipCalculator,
    SwapRate,
    MarginRequirement,
    ForexMarketCalendar,
    ForexPairConfiguration,
)


class TestForexPair(unittest.TestCase):
    def test_from_symbol(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.base, "EUR")
        self.assertEqual(pair.quote, "USD")

    def test_from_symbol_without_slash(self):
        pair = ForexPair.from_symbol("GBPUSD")
        self.assertEqual(pair.base, "GBP")
        self.assertEqual(pair.quote, "USD")

    def test_repr(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertIn("EUR/USD", repr(pair))

    def test_is_jpy_pair_true(self):
        pair = ForexPair.from_symbol("USD/JPY")
        self.assertTrue(pair.is_jpy_pair())

    def test_is_jpy_pair_false(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertFalse(pair.is_jpy_pair())

    def test_inverse_pair(self):
        pair = ForexPair.from_symbol("EUR/USD")
        inverse = pair.inverse_pair()
        self.assertEqual(inverse.base, "USD")
        self.assertEqual(inverse.quote, "EUR")

    def test_to_oanda_format(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.to_oanda_format(), "EUR_USD")

    def test_from_oanda_format(self):
        pair = ForexPair.from_oanda_format("EUR_USD")
        self.assertEqual(pair.base, "EUR")
        self.assertEqual(pair.quote, "USD")

    def test_to_yahoo_format(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.to_yahoo_format(), "EURUSD=X")

    def test_to_polygon_format(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.to_polygon_format(), "C:EURUSD")

    def test_get_symbol(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.get_symbol(), "EUR/USD")

    def test_pip_decimal_places_non_jpy(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.pip_decimal_places, 4)

    def test_pip_decimal_places_jpy(self):
        pair = ForexPair.from_symbol("USD/JPY")
        self.assertEqual(pair.pip_decimal_places, 2)

    def test_display_decimal_places_non_jpy(self):
        pair = ForexPair.from_symbol("EUR/USD")
        self.assertEqual(pair.display_decimal_places, 5)

    def test_display_decimal_places_jpy(self):
        pair = ForexPair.from_symbol("USD/JPY")
        self.assertEqual(pair.display_decimal_places, 3)

    def test_normalize_symbol_with_dash(self):
        self.assertEqual(
            ForexPair.normalize_symbol("EUR-USD"), "EUR/USD"
        )

    def test_normalize_symbol_with_underscore(self):
        self.assertEqual(
            ForexPair.normalize_symbol("EUR_USD"), "EUR/USD"
        )

    def test_immutable(self):
        pair = ForexPair.from_symbol("EUR/USD")
        with self.assertRaises(FrozenInstanceError):
            pair.base = "GBP"


class TestLotSize(unittest.TestCase):
    def test_standard_lot_units(self):
        self.assertEqual(LotSize.STANDARD.to_units(), 100_000)

    def test_mini_lot_units(self):
        self.assertEqual(LotSize.MINI.to_units(), 10_000)

    def test_micro_lot_units(self):
        self.assertEqual(LotSize.MICRO.to_units(), 1_000)

    def test_from_units_standard(self):
        self.assertEqual(LotSize.from_units(100000), LotSize.STANDARD)

    def test_from_units_mini(self):
        self.assertEqual(LotSize.from_units(10000), LotSize.MINI)

    def test_from_units_micro(self):
        self.assertEqual(LotSize.from_units(1000), LotSize.MICRO)

    def test_from_units_invalid(self):
        with self.assertRaises(ValueError):
            LotSize.from_units(500)

    def test_to_decimal(self):
        self.assertEqual(LotSize.STANDARD.to_decimal(), Decimal("100000"))


class TestPipCalculator(unittest.TestCase):
    def setUp(self):
        self.eur_usd = ForexPair.from_symbol("EUR/USD")
        self.usd_jpy = ForexPair.from_symbol("USD/JPY")

    def test_pip_value_standard_lot(self):
        value = PipCalculator.pip_value(self.eur_usd, LotSize.STANDARD)
        self.assertEqual(value, Decimal("10.0"))

    def test_pip_value_mini_lot(self):
        value = PipCalculator.pip_value(self.eur_usd, LotSize.MINI)
        self.assertEqual(value, Decimal("1.0"))

    def test_pip_value_micro_lot(self):
        value = PipCalculator.pip_value(self.eur_usd, LotSize.MICRO)
        self.assertEqual(value, Decimal("0.10"))

    def test_pip_value_with_units_int(self):
        value = PipCalculator.pip_value(self.eur_usd, 100000)
        self.assertEqual(value, Decimal("10.0"))

    def test_price_to_pips_non_jpy(self):
        pips = PipCalculator.price_to_pips(
            self.eur_usd,
            Decimal("1.1050"),
            Decimal("1.1060"),
        )
        self.assertEqual(pips, Decimal("10.00"))

    def test_price_to_pips_jpy(self):
        pips = PipCalculator.price_to_pips(
            self.usd_jpy,
            Decimal("110.50"),
            Decimal("110.60"),
        )
        self.assertEqual(pips, Decimal("10.00"))

    def test_pips_to_price_non_jpy(self):
        price = PipCalculator.pips_to_price(
            self.eur_usd, Decimal("1.1000"), Decimal("50")
        )
        self.assertEqual(price, Decimal("1.1050"))

    def test_pips_to_price_jpy(self):
        price = PipCalculator.pips_to_price(
            self.usd_jpy, Decimal("110.00"), Decimal("50")
        )
        self.assertEqual(price, Decimal("110.50"))

    def test_calculate_pnl(self):
        result = PipCalculator.calculate_pnl(
            self.eur_usd,
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1100"),
            units=LotSize.STANDARD,
        )
        self.assertEqual(result["pips"], Decimal("100.00"))
        self.assertEqual(result["pip_value"], Decimal("10.0"))


class TestSwapRate(unittest.TestCase):
    def setUp(self):
        self.eur_usd = ForexPair.from_symbol("EUR/USD")

    def test_swap_rate_creation(self):
        rate = SwapRate(pair=self.eur_usd, long_rate=Decimal("-3.5"))
        self.assertEqual(rate.pair, self.eur_usd)
        self.assertEqual(rate.long_rate, Decimal("-3.5"))
        self.assertEqual(rate.short_rate, Decimal("0"))

    def test_swap_rate_long_short(self):
        rate = SwapRate(
            pair=self.eur_usd,
            long_rate=Decimal("-3.5"),
            short_rate=Decimal("-1.2"),
        )
        self.assertEqual(rate.long_rate, Decimal("-3.5"))
        self.assertEqual(rate.short_rate, Decimal("-1.2"))

    def test_calculate_swap_long(self):
        rate = SwapRate(pair=self.eur_usd, long_rate=Decimal("-3.5"))
        swap = rate.calculate_swap(
            side="BUY", units=Decimal("100000")
        )
        self.assertEqual(swap, Decimal("-3.50"))

    def test_calculate_swap_short(self):
        rate = SwapRate(
            pair=self.eur_usd,
            long_rate=Decimal("-3.5"),
            short_rate=Decimal("-1.2"),
        )
        swap = rate.calculate_swap(
            side="SELL", units=Decimal("100000")
        )
        self.assertEqual(swap, Decimal("-1.20"))

    def test_calculate_swap_held_through_wednesday(self):
        rate = SwapRate(pair=self.eur_usd, long_rate=Decimal("-3.5"))
        swap = rate.calculate_swap(
            side="BUY",
            units=Decimal("100000"),
            held_through_wednesday=True,
        )
        self.assertEqual(swap, Decimal("-10.50"))

    def test_calculate_swap_zero_days(self):
        rate = SwapRate(pair=self.eur_usd, long_rate=Decimal("-3.5"))
        swap = rate.calculate_swap(
            side="BUY", units=Decimal("100000"), days_held=0
        )
        self.assertEqual(swap, Decimal("0"))

    def test_supports_pair(self):
        rate = SwapRate(pair=self.eur_usd)
        other = ForexPair.from_symbol("GBP/USD")
        self.assertTrue(rate.supports_pair(self.eur_usd))
        self.assertFalse(rate.supports_pair(other))


class TestMarginRequirement(unittest.TestCase):
    def setUp(self):
        self.eur_usd = ForexPair.from_symbol("EUR/USD")

    def test_margin_requirement_default_leverage(self):
        margin = MarginRequirement(pair=self.eur_usd)
        self.assertEqual(margin.leverage, 30)
        self.assertEqual(margin.pair, self.eur_usd)

    def test_margin_requirement_custom_leverage(self):
        margin = MarginRequirement(pair=self.eur_usd, leverage=50)
        self.assertEqual(margin.leverage, 50)

    def test_margin_rate(self):
        margin = MarginRequirement(pair=self.eur_usd, leverage=30)
        expected = Decimal("1") / Decimal("30")
        self.assertEqual(margin.margin_rate, expected)

    def test_margin_rate_custom(self):
        margin = MarginRequirement(pair=self.eur_usd, leverage=50)
        expected = Decimal("1") / Decimal("50")
        self.assertEqual(margin.margin_rate, expected)

    def test_required_margin(self):
        margin = MarginRequirement(pair=self.eur_usd, leverage=30)
        required = margin.required_margin(Decimal("100000"))
        self.assertEqual(required, Decimal("3333.33"))

    def test_required_margin_50x(self):
        margin = MarginRequirement(pair=self.eur_usd, leverage=50)
        required = margin.required_margin(Decimal("100000"))
        self.assertEqual(required, Decimal("2000.00"))

    def test_supports_pair(self):
        margin = MarginRequirement(pair=self.eur_usd)
        other = ForexPair.from_symbol("GBP/USD")
        self.assertTrue(margin.supports_pair(self.eur_usd))
        self.assertFalse(margin.supports_pair(other))

    def test_zero_leverage_raises(self):
        with self.assertRaises(ValueError):
            MarginRequirement(pair=self.eur_usd, leverage=0).margin_rate


class TestForexMarketCalendar(unittest.TestCase):
    def test_is_open_monday(self):
        dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(ForexMarketCalendar.is_market_open(dt))

    def test_is_open_friday_before_close(self):
        dt = datetime(2024, 1, 5, 20, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(ForexMarketCalendar.is_market_open(dt))

    def test_is_closed_saturday(self):
        dt = datetime(2024, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        self.assertFalse(ForexMarketCalendar.is_market_open(dt))

    def test_is_closed_sunday_before_open(self):
        dt = datetime(2024, 1, 7, 20, 59, 0, tzinfo=timezone.utc)
        self.assertFalse(ForexMarketCalendar.is_market_open(dt))

    def test_is_open_sunday_after_open(self):
        dt = datetime(2024, 1, 7, 22, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(ForexMarketCalendar.is_market_open(dt))

    def test_is_closed_friday_after_close(self):
        dt = datetime(2024, 1, 5, 22, 0, 0, tzinfo=timezone.utc)
        self.assertFalse(ForexMarketCalendar.is_market_open(dt))

    def test_next_market_open_from_closed(self):
        saturday = datetime(2024, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        next_open = ForexMarketCalendar.next_market_open(saturday)
        expected = datetime(2024, 1, 7, 21, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(next_open, expected)

    def test_next_market_open_from_open(self):
        monday = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        next_open = ForexMarketCalendar.next_market_open(monday)
        self.assertEqual(next_open, monday)

    def test_is_open_edge_sunday_2100(self):
        dt = datetime(2024, 1, 7, 21, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(ForexMarketCalendar.is_market_open(dt))

    def test_is_open_edge_friday_2100(self):
        dt = datetime(2024, 1, 5, 21, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(ForexMarketCalendar.is_market_open(dt))

    def test_previous_market_close_saturday(self):
        saturday = datetime(2024, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        prev_close = ForexMarketCalendar.previous_market_close(saturday)
        expected = datetime(2024, 1, 5, 21, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(prev_close, expected)


class TestForexPairConfiguration(unittest.TestCase):
    def test_default_configuration(self):
        config = ForexPairConfiguration(symbol="EUR/USD")
        self.assertEqual(config.symbol, "EUR/USD")
        self.assertEqual(config.pair.base, "EUR")
        self.assertEqual(config.pair.quote, "USD")
        self.assertEqual(config.margin_leverage, 30)
        self.assertEqual(config.default_lot_size, LotSize.MICRO)

    def test_custom_configuration(self):
        config = ForexPairConfiguration(
            symbol="GBP/USD",
            swap_long_rate=Decimal("-3.5"),
            swap_short_rate=Decimal("-1.2"),
            margin_leverage=50,
            default_lot_size=LotSize.MINI,
        )
        self.assertEqual(config.symbol, "GBP/USD")
        self.assertEqual(config.margin_leverage, 50)
        self.assertEqual(config.default_lot_size, LotSize.MINI)

    def test_to_swap_rate(self):
        config = ForexPairConfiguration(
            symbol="EUR/USD",
            swap_long_rate=Decimal("-3.5"),
        )
        swap = config.to_swap_rate()
        self.assertIsNotNone(swap)
        self.assertEqual(swap.long_rate, Decimal("-3.5"))

    def test_to_swap_rate_none(self):
        config = ForexPairConfiguration(symbol="EUR/USD")
        swap = config.to_swap_rate()
        self.assertIsNone(swap)

    def test_to_margin_requirement(self):
        config = ForexPairConfiguration(
            symbol="EUR/USD", margin_leverage=50
        )
        margin = config.to_margin_requirement()
        self.assertEqual(margin.leverage, 50)


if __name__ == "__main__":
    unittest.main()
