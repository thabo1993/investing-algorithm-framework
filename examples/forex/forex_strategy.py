"""
Example: EUR/USD SMA Crossover Strategy with Oanda Live Wiring.

Demonstrates:
  - ForexPair and PipCalculator for pip-based P&L tracking
  - SwapTracker for overnight rollover cost tracking
  - MarginUtilization for position sizing within leverage limits
  - apply_market_calendar_filter to restrict trading to forex market hours
  - OandaOHLCVDataProvider / OandaOrderExecutor for live trading
  - add_forex_pair_configuration() on the App

Before running:
  1. pip install investing-algorithm-framework[oanda]
  2. Set environment variables:
       OANDA_API_KEY=<your_api_key>
       OANDA_ACCOUNT_ID=<your_account_id>
       OANDA_ENVIRONMENT=practice (or live)
"""

import os
from decimal import Decimal
from datetime import datetime, timezone

import polars as pl

from investing_algorithm_framework import App, TradingStrategy
from investing_algorithm_framework.domain import (
    TimeFrame,
    OrderSide,
    OrderType,
    Order,
)
from investing_algorithm_framework.domain.models.forex import (
    ForexPair,
    LotSize,
    ForexPairConfiguration,
)
from investing_algorithm_framework.domain.backtesting import (
    calculate_pip_pnl,
    SwapTracker,
    calculate_margin_utilization,
    apply_market_calendar_filter,
)
from investing_algorithm_framework.infrastructure import (
    OandaOHLCVDataProvider,
    OandaOrderExecutor,
    OandaPortfolioProvider,
)

SYMBOL = "EUR/USD"
SMA_SHORT = 5
SMA_LONG = 20

app = App(name="forex_sma_crossover")


class ForexSmaCrossover(TradingStrategy):
    def apply_strategy(self, algorithm, **kwargs):
        data = algorithm.get_ohlcv(symbol=SYMBOL, time_frame=TimeFrame.H1)

        if data is None or len(data) < SMA_LONG:
            return

        df = data.to_polars()
        df = apply_market_calendar_filter(
            df, market="FOREX", datetime_column="Datetime"
        )
        if len(df) < SMA_LONG:
            return

        closes = df["close"].to_list()
        sma_short_val = sum(closes[-SMA_SHORT:]) / SMA_SHORT
        sma_long_val = sum(closes[-SMA_LONG:]) / SMA_LONG

        position = algorithm.get_position(symbol=SYMBOL)

        if position is None and sma_short_val > sma_long_val:
            pair = ForexPair.from_symbol(SYMBOL)

            notional = Decimal("10000")
            margin = calculate_margin_utilization(
                position_notional=notional,
                account_balance=algorithm.get_portfolio().get_total_balance(),
                leverage=30,
            )

            if not margin.is_margin_call:
                algorithm.create_limit_order(
                    symbol=SYMBOL,
                    price=closes[-1],
                    amount=notional,
                    order_side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                )

        elif position is not None and sma_short_val < sma_long_val:
            entry = Decimal(str(position.get_cost_basis()))
            exit_price = Decimal(str(closes[-1]))
            pair = ForexPair.from_symbol(SYMBOL)

            pnl = calculate_pip_pnl(
                entry_price=entry,
                exit_price=exit_price,
                pair=pair,
                units=Decimal(str(abs(position.get_amount()))),
            )

            algorithm.create_limit_order(
                symbol=SYMBOL,
                price=closes[-1],
                amount=abs(position.get_amount()),
                order_side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
            )


def configure_live(app: App):
    api_key = os.environ["OANDA_API_KEY"]
    account_id = os.environ["OANDA_ACCOUNT_ID"]
    environment = os.environ.get("OANDA_ENVIRONMENT", "practice")

    app.add_forex_pair_configuration(
        ForexPairConfiguration(
            symbol=SYMBOL,
            swap_long_rate=Decimal("-3.5"),
            swap_short_rate=Decimal("1.2"),
            margin_leverage=30,
            default_lot_size=LotSize.MICRO,
        )
    )

    app.add_data_provider(
        OandaOHLCVDataProvider(
            api_key=api_key,
            environment=environment,
        )
    )
    app.add_order_executor(
        OandaOrderExecutor(
            api_key=api_key,
            account_id=account_id,
            environment=environment,
        )
    )
    app.add_portfolio_provider(
        OandaPortfolioProvider(
            api_key=api_key,
            account_id=account_id,
            environment=environment,
        )
    )
    app.add_market(
        market="FOREX",
        trading_symbol=SYMBOL,
        initial_balance=10000,
    )


def configure_backtest(app: App):
    app.add_forex_pair_configuration(
        ForexPairConfiguration(
            symbol=SYMBOL,
            swap_long_rate=Decimal("-3.5"),
            swap_short_rate=Decimal("1.2"),
            margin_leverage=30,
            default_lot_size=LotSize.MICRO,
        )
    )

    app.add_market(
        market="FOREX",
        trading_symbol=SYMBOL,
        initial_balance=10000,
    )


if __name__ == "__main__":
    if os.environ.get("OANDA_API_KEY"):
        configure_live(app)
    else:
        configure_backtest(app)

    app.add_strategy(ForexSmaCrossover)
    app.run()
