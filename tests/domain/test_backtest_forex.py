import unittest
from decimal import Decimal
from datetime import datetime, timezone

import polars as pl

from investing_algorithm_framework.domain.backtesting import (
    PipPnLResult,
    calculate_pip_pnl,
    SwapTracker,
    calculate_margin_utilization,
    MarginUtilizationResult,
    apply_market_calendar_filter,
)
from investing_algorithm_framework.domain.models.forex import (
    ForexPair,
    LotSize,
    SwapRate,
    ForexMarketCalendar,
)
from investing_algorithm_framework.domain.models.order.order_side import (
    OrderSide,
)


class TestPipPnL(unittest.TestCase):

    def setUp(self):
        self.eur_usd = ForexPair.from_symbol("EUR/USD")
        self.usd_jpy = ForexPair.from_symbol("USD/JPY")

    def test_calculate_pip_pnl_long(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1050"),
            pair=self.eur_usd,
            units=Decimal("10000"),
        )
        self.assertEqual(result.pips, Decimal("50"))
        self.assertAlmostEqual(
            float(result.base_currency_pnl), 50.0, places=2
        )

    def test_calculate_pip_pnl_short(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("1.1050"),
            exit_price=Decimal("1.1000"),
            pair=self.eur_usd,
            units=Decimal("10000"),
        )
        self.assertEqual(result.pips, Decimal("-50"))
        self.assertEqual(
            result.base_currency_pnl, Decimal("-50.00")
        )

    def test_calculate_pip_pnl_jpy_pair(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("110.00"),
            exit_price=Decimal("110.50"),
            pair=self.usd_jpy,
            units=Decimal("10000"),
        )
        self.assertEqual(result.pips, Decimal("50"))
        self.assertAlmostEqual(
            float(result.base_currency_pnl), 5000.0, places=0
        )

    def test_calculate_pip_pnl_with_lot_size(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1010"),
            pair=self.eur_usd,
            units=LotSize.STANDARD,
        )
        self.assertEqual(result.pips, Decimal("10"))
        self.assertAlmostEqual(
            float(result.base_currency_pnl), 100.0, places=0
        )

    def test_calculate_pip_pnl_with_quote_to_base_rate(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1050"),
            pair=self.eur_usd,
            units=Decimal("10000"),
            quote_to_base_rate=Decimal("0.85"),
        )
        self.assertEqual(result.pips, Decimal("50"))
        self.assertEqual(
            result.base_currency_pnl, Decimal("42.50")
        )

    def test_zero_pips(self):
        result = calculate_pip_pnl(
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1000"),
            pair=self.eur_usd,
            units=Decimal("10000"),
        )
        self.assertEqual(result.pips, Decimal("0"))
        self.assertEqual(result.base_currency_pnl, Decimal("0.00"))


class TestSwapTracker(unittest.TestCase):

    def setUp(self):
        self.eur_usd = ForexPair.from_symbol("EUR/USD")
        self.swap_rate = SwapRate(
            pair=self.eur_usd,
            long_rate=Decimal("-3.5"),
            short_rate=Decimal("1.2"),
        )
        self.tracker = SwapTracker()
        self.tracker.configure(self.eur_usd, self.swap_rate)

    def test_configure_and_get_swap_rate(self):
        rate = self.tracker.get_swap_rate("EUR/USD")
        self.assertIsNotNone(rate)
        self.assertEqual(rate.long_rate, Decimal("-3.5"))

    def test_calculate_rollover_swap_long(self):
        swap = self.tracker.calculate_rollover_swap(
            pair=self.eur_usd,
            side="long",
            units=Decimal("10000"),
            position_held_at_rollover=True,
        )
        self.assertEqual(swap, self.swap_rate.calculate_swap(
            side=OrderSide.BUY, units=Decimal("10000"), days_held=1,
        ))

    def test_calculate_rollover_swap_no_position(self):
        swap = self.tracker.calculate_rollover_swap(
            pair=self.eur_usd,
            side=OrderSide.BUY,
            units=Decimal("10000"),
            position_held_at_rollover=False,
        )
        self.assertEqual(swap, Decimal("0"))

    def test_calculate_rollover_swap_no_rate(self):
        tracker = SwapTracker()
        swap = tracker.calculate_rollover_swap(
            pair=self.eur_usd,
            side=OrderSide.BUY,
            units=Decimal("10000"),
            position_held_at_rollover=True,
        )
        self.assertEqual(swap, Decimal("0"))

    def test_calculate_swap_for_date_range(self):
        total = self.tracker.calculate_swap_for_date_range(
            pair=self.eur_usd,
            side="long",
            units=Decimal("10000"),
            entry_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            exit_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        )
        self.assertLess(total, Decimal("0"))


class TestMarginUtilization(unittest.TestCase):

    def test_basic_margin_calculation(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("100000"),
            account_balance=Decimal("10000"),
            leverage=30,
        )
        self.assertAlmostEqual(
            float(result.margin_used), 3333.33, places=2
        )
        self.assertAlmostEqual(
            float(result.margin_available), 6666.67, places=2
        )
        self.assertAlmostEqual(result.utilization_percentage, 33.33, places=1)
        self.assertEqual(result.leverage, 30)
        self.assertFalse(result.is_margin_call)

    def test_margin_call_detected(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("300000"),
            account_balance=Decimal("10000"),
            leverage=30,
        )
        self.assertTrue(result.is_margin_call)

    def test_zero_balance(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("0"),
            account_balance=Decimal("0"),
            leverage=30,
        )
        self.assertFalse(result.is_margin_call)
        self.assertEqual(result.utilization_percentage, 0.0)

    def test_negative_leverage_raises(self):
        with self.assertRaises(ValueError):
            calculate_margin_utilization(
                position_notional=Decimal("1000"),
                account_balance=Decimal("1000"),
                leverage=-1,
            )

    def test_leverage_1(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("10000"),
            account_balance=Decimal("10000"),
            leverage=1,
        )
        self.assertEqual(result.margin_used, Decimal("10000.00"))
        self.assertTrue(result.is_margin_call)

    def test_high_leverage_small_margin(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("100000"),
            account_balance=Decimal("10000"),
            leverage=100,
        )
        self.assertAlmostEqual(
            float(result.margin_used), 1000.00, places=2
        )
        self.assertAlmostEqual(
            float(result.utilization_percentage), 10.0, places=1
        )

    def test_result_is_dataclass(self):
        result = calculate_margin_utilization(
            position_notional=Decimal("50000"),
            account_balance=Decimal("20000"),
            leverage=30,
        )
        self.assertIsInstance(result, MarginUtilizationResult)
        self.assertTrue(hasattr(result, "margin_used"))
        self.assertTrue(hasattr(result, "margin_available"))
        self.assertTrue(hasattr(result, "utilization_percentage"))
        self.assertTrue(hasattr(result, "leverage"))
        self.assertTrue(hasattr(result, "is_margin_call"))


class TestMarketCalendarFilter(unittest.TestCase):

    def test_non_forex_market_passthrough(self):
        df = pl.DataFrame({"Datetime": [datetime(2024, 1, 6)], "close": [1.0]})
        result = apply_market_calendar_filter(df, market="STOCK")
        self.assertEqual(len(result), 1)

    def test_forex_filter_removes_weekend(self):
        saturday = datetime(2024, 1, 6, tzinfo=timezone.utc)
        monday = datetime(2024, 1, 8, tzinfo=timezone.utc)
        df = pl.DataFrame({
            "Datetime": [saturday, monday],
            "close": [1.0, 1.1],
        })
        result = apply_market_calendar_filter(
            df, market="FOREX", datetime_column="Datetime"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result["close"][0], 1.1)

    def test_forex_filter_all_open(self):
        thursday = datetime(2024, 1, 4, 14, 0, 0, tzinfo=timezone.utc)
        df = pl.DataFrame({
            "Datetime": [thursday],
            "close": [1.0],
        })
        result = apply_market_calendar_filter(
            df, market="FOREX", datetime_column="Datetime"
        )
        self.assertEqual(len(result), 1)

    def test_forex_filter_missing_column(self):
        df = pl.DataFrame({"close": [1.0]})
        result = apply_market_calendar_filter(
            df, market="FOREX", datetime_column="Datetime"
        )
        self.assertEqual(len(result), 1)

    def test_empty_dataframe(self):
        df = pl.DataFrame({
            "Datetime": [],
            "close": [],
        })
        result = apply_market_calendar_filter(
            df, market="FOREX", datetime_column="Datetime"
        )
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
