# Implementation Plan: FOREX Trading Support

**Branch:** `001-forex-support` | **Spec:** `specs/001-forex-support/spec.md` | **Date:** 2026-07-04

> The **how**. Derived from `spec.md`. All `[NEEDS CLARIFICATION]` items have been resolved
> (see §Resolved Clarifications). This plan, plus `research.md`, is the input to `/agent-tasks`.

---

## Resolved Clarifications

| Spec Marker | Resolution |
|---|---|
| JPY pair decimal places | JPY pairs display **3 decimal places** (154.250), matching modern broker convention and Oanda's default. |
| Default swap cost | **Zero swap cost** when not configured. Users explicitly configure swap rates for pairs they care about. Predictable, no silent surprises. |
| Forex pair configuration model | **New `ForexPairConfiguration` model** — separate from `MarketCredential` and `DataSource`. Clean separation of concerns. |

---

## 1. Capacity & Access Patterns

### Assumptions
- **Scale:** Single-user to small-team algorithmic trading (1–50 strategies, 1–20 currency pairs).
- **Data fetch pattern:** OHLCV data downloaded once per backtest run, then cached locally.
  Live data polled every 1–60 minutes depending on strategy timeframe.
- **Trade frequency:** 1–100 trades/day per strategy. Not high-frequency.
- **Read/write ratio:** Heavy read (historical data, 95%), light write (orders, 5%).
- **Dominant queries:**
  1. `get_data(symbol="EUR/USD", market="FOREX", time_frame="1h", start=..., end=...)` — OHLCV fetch
  2. `execute_order(order, portfolio, credential)` — order placement (weight ≈ 1)
  3. `get_position(portfolio, symbol, credential)` — portfolio sync (weight ≈ 10)
  4. `get_rate(from_currency, to_currency, date)` — FX rate for portfolio valuation

### Traffic Shape
- Backtesting: burst download (pre-backtest data preparation), then sequential per-index reads
  from local cache.
- Live trading: steady low-frequency polling, plus order execution on strategy decisions.

---

## 2. System Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Application (App)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ DataProvider  │  │  OrderExec   │  │  PortfolioProvider       │  │
│  │  Service      │  │  Lookup      │  │  Lookup                  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬──────────────┘  │
│         │                  │                      │                 │
│  ┌──────┴──────────────────┴──────────────────────┴───────────┐    │
│  │                    FXRateProvider                          │    │
│  │           (multi-currency portfolio valuation)             │    │
│  └────────────────────────────────────────────────────────────┘    │
│         │                  │                      │                 │
│         ▼                  ▼                      ▼                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │ FRED OHLCV   │  │ OandaOrder   │  │ OandaPortfolio       │     │
│  │ Provider     │  │ Executor     │  │ Provider             │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────────────┤     │
│  │ Twelve Data  │  │ (Oanda v20)  │  │ (Oanda v20 positions) │     │
│  │ OHLCV Prov.  │  │              │  │                      │     │
│  ├──────────────┤  └──────────────┘  │ CCXTPortfolioProv.   │     │
│  │ ExchangeRate │                     │ (existing)           │     │
│  │ API Ticker   │                     └──────────────────────┘     │
│  ├──────────────┤                                                  │
│  │ Oanda OHLCV  │  ┌────────────────────────────────────────┐     │
│  │ Provider     │  │ Forex Models & Utilities               │     │
│  ├──────────────┤  │  ForexPair │ LotSize │ PipCalculator   │     │
│  │ Yahoo (exist)│  │  SwapRate  │ Margin  │ MarketCalendar  │     │
│  │ Poly (exist) │  │  ForexPairConfiguration                 │     │
│  │ AV (exist)   │  └────────────────────────────────────────┘     │
│  └──────────────┘                                                  │
│         │                                                          │
│         ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                   Backtest Engine (enhanced)               │   │
│  │   ┌───────────────┐ ┌──────────────┐ ┌────────────────┐   │   │
│  │   │ MarketCalendar │ │ PipPnL Calc  │ │ SwapTracker    │   │   │
│  │   │ (24/5 filter)  │ │ (pip-based)  │ │ (overnight)    │   │   │
│  │   └───────────────┘ └──────────────┘ └────────────────┘   │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Patterns
- **Data Providers → App:** Synchronous via `DataProviderService.get(data_source)`. Data
  providers are called by the framework, not the other way around.
- **Order Executor → Broker:** Synchronous HTTP (Oanda v20 REST API). Wrapped with retry
  logic and graceful error handling per spec.
- **Portfolio Provider → Broker:** Synchronous HTTP. Portfolio sync runs on timer.
- **FXRateProvider → App:** In-process call for each portfolio valuation.
- **Backtest Engine → Data Providers:** Synchronous, but data is pre-loaded (not fetched
  per index tick). The engine reads from in-memory Polars DataFrames.

### State Ownership
| Component | Owns | Scaling Story |
|-----------|------|---------------|
| Data Providers | API credentials, cached DataFrames | Stateless — each DataSource gets a `copy()`. Cache is local CSV. |
| Order Executor | Oanda API connection state | Stateless — HTTP requests per operation. |
| Portfolio Provider | Oanda positions (pulled, not pushed) | Stateless — reads from Oanda on demand. |
| FXRateProvider | No persistent state | Stateless — fetches rates live or from config. |
| Forex Models (`ForexPair`, etc.) | No state (value objects) | Stateless — pure computation. |
| Backtest Engine | Loaded DataFrames per strategy run | Memory-bound by data window `warmup_window`. Scaling seam: disk-backed sliding window. |

---

## 3. Component Structure

### 3.1 New Domain Models (`investing_algorithm_framework/domain/models/forex/`)

#### `ForexPair`
Value object representing a currency pair with forex-specific metadata.

```python
@dataclass(frozen=True)
class ForexPair:
    base_currency: str    # e.g. "EUR"
    quote_currency: str   # e.g. "USD"
    symbol: str           # normalized: "EUR/USD"

    # Derived
    pip_decimal_places: int = 4    # 4 for most, 2 for JPY pairs
    display_decimal_places: int = 5  # 5 for most, 3 for JPY pairs

    @staticmethod
    def from_symbol(symbol: str) -> "ForexPair"
    def normalize_symbol(symbol: str) -> str  # "EURUSD" → "EUR/USD"
    def to_oanda_format() -> str              # "EUR/USD" → "EUR_USD"
    def to_yahoo_format() -> str              # "EUR/USD" → "EURUSD=X"
    def to_polygon_format() -> str            # "EUR/USD" → "C:EURUSD"
    def is_jpy_pair() -> bool
    def inverse_pair() -> "ForexPair"          # USD/JPY → JPY/USD
```

#### `LotSize`
Value enum with unit conversion.

```python
class LotSize(Enum):
    STANDARD = 100000  # 100k units
    MINI = 10000       # 10k units
    MICRO = 1000       # 1k units

    @staticmethod
    def from_units(units: float) -> "LotSize"
    def to_units(self) -> int
```

#### `PipCalculator`
Pure function utility for pip-based price calculations.

```python
class PipCalculator:
    @staticmethod
    def price_to_pips(pair: ForexPair, entry: Decimal, exit: Decimal) -> Decimal
    @staticmethod
    def pips_to_price(pair: ForexPair, price: Decimal, pips: Decimal) -> Decimal
    @staticmethod
    def pip_value(pair: ForexPair, units: Decimal, quote_to_base_rate: Decimal) -> Decimal
    @staticmethod
    def format_price(pair: ForexPair, price: Decimal) -> str
```

#### `SwapRate`
Data model for overnight rollover costs.

```python
@dataclass
class SwapRate:
    pair: ForexPair
    long_rate: Decimal       # pips credited/debited per lot held long overnight
    short_rate: Decimal      # pips credited/debited per lot held short overnight
    triple_swap_wednesday: bool = True  # 3x rate on Wednesday rollover

    def calculate_swap(
        self, side: OrderSide, units: Decimal, days_held: int,
        held_through_wednesday: bool
    ) -> Decimal
```

#### `MarginRequirement`
Data model for margin.

```python
@dataclass
class MarginRequirement:
    pair: ForexPair
    leverage: Decimal                # e.g. 30.0 (1:30)
    margin_rate: Decimal             # derived: 1/leverage, e.g. 0.03333

    def required_margin(self, notional: Decimal) -> Decimal
```

#### `ForexMarketCalendar`
Utility for 24/5 market hours.

```python
class ForexMarketCalendar:
    WEEKEND_DAYS = {5, 6}  # Saturday, Sunday (ISO weekday)

    @staticmethod
    def is_market_open(dt: datetime) -> bool
    @staticmethod
    def filter_market_hours(df: pl.DataFrame) -> pl.DataFrame
    @staticmethod
    def next_market_open(dt: datetime) -> datetime
    @staticmethod
    def previous_market_close(dt: datetime) -> datetime
```

#### `ForexPairConfiguration`
User-facing config model for per-pair forex parameters.

```python
@dataclass
class ForexPairConfiguration:
    symbol: str                    # "EUR/USD"
    pip_decimal_places: int = 4    # override default
    display_decimal_places: int = 5
    swap_long_rate: Decimal = 0
    swap_short_rate: Decimal = 0
    margin_leverage: Decimal = 30  # default ESMA
    default_lot_size: LotSize = LotSize.MICRO
```

### 3.2 New Data Providers

All new providers follow the existing `OHLCVDataProviderBase` pattern unless noted.

#### `FREDOHLCVDataProvider` (`infrastructure/data_providers/fred.py`)
- Extends: `OHLCVDataProviderBase`
- `market_name = "FRED"`
- Timeframes: `{"1d": "d"}` (daily only)
- OHLC data: sets Open=High=Low=Close=same observation value. Volume=0.
- Symbol mapping dictionary `EUR/USD → DEXUSEU` etc.
- Auth: `MarketCredential(market="FRED", api_key=...)`

#### `TwelveDataOHLCVDataProvider` (`infrastructure/data_providers/twelve_data.py`)
- Extends: `OHLCVDataProviderBase`
- `market_name = "TWELVEDATA"`
- Full timeframe support (1m → 1M)
- Auth: `MarketCredential(market="TWELVEDATA", api_key=...)`
- Rate limit: 800/day, track via response, graceful degradation

#### `ExchangeRateAPITickerDataProvider` (`infrastructure/data_providers/exchange_rate_api.py`)
- Extends: `DataProvider` (not OHLCVBase — no OHLCV support on free tier)
- `data_type = DataType.TICKER`
- `data_provider_identifier = "exchange_rate_api_ticker_provider"`
- `market_name = "EXCHANGE_RATE_API"`
- Provides current/latest rate as ticker data
- Auth: `MarketCredential(market="EXCHANGE_RATE_API", api_key=...)`

#### `OandaOHLCVDataProvider` (`infrastructure/data_providers/oanda.py`)
- Extends: `OHLCVDataProviderBase`
- `market_name = "OANDA"`
- Uses `/v3/accounts/{id}/candles/{instrument}` endpoint
- Timeframe mapping: 1m= M1, 5m= M5, 1h= H1, 1d= D, 1W= W, 1M= M
- Auth: `MarketCredential(market="OANDA", api_key=..., secret_key=<account_id>)`
  (api_key = Bearer token, secret_key = account ID)

#### `OandaTickerDataProvider` (`infrastructure/data_providers/oanda.py`)
- Extends: `DataProvider`
- `data_type = DataType.TICKER`
- Uses `/v3/accounts/{id}/pricing` endpoint
- Returns bid/ask/mid prices

### 3.3 Oanda Broker Integration

#### `OandaOrderExecutor` (`infrastructure/order_executors/oanda_order_executor.py`)
- Implements: `OrderExecutor`
- `supports_market(market)`: returns True for `"OANDA"`
- `execute_order(portfolio, order, market_credential)`:
  - Normalizes `EUR/USD` → `EUR_USD`
  - Maps framework order types to Oanda v20 order types
  - Supports attached TP/SL via `takeProfitOnFill` / `stopLossOnFill`
  - Handles `429` with retry and backoff (per spec NFR-003)
  - Returns `Order` with `external_id` set to Oanda transaction ID
  - On error: returns `Order(status=FAILED)` per abstract contract
- `cancel_order(portfolio, order, market_credential)`:
  - Sends `PUT .../cancel` to Oanda
  - Handles already-filled/cancelled gracefully

#### `OandaPortfolioProvider` (`infrastructure/portfolio_providers/oanda_portfolio_provider.py`)
- Implements: `PortfolioProvider`
- `supports_market(market)`: returns True for `"OANDA"`
- `get_order(portfolio, order, market_credential)`:
  - Fetches order status from `/v3/accounts/{id}/orders/{order_id}`
  - Returns updated `Order` or `None`
- `get_position(portfolio, symbol, market_credential)`:
  - Fetches from `/v3/accounts/{id}/positions/{instrument}`
  - Returns `Position(symbol, amount, cost)` or `None`
  - Includes unrealized P&L in position metadata

#### `OandaFXRateProvider` (`infrastructure/fx_providers/oanda_fx_rate_provider.py`)
- Implements: `FXRateProvider`
- Fetches live pricing from Oanda v20 `/pricing` endpoint
- Uses midpoint (bid+ask)/2 as the rate
- Falls back to `StaticFXRateProvider`-style inverted rate lookup
- Supports `get_rate(from_currency, to_currency, date=None)`:
  - For `EUR/USD`: gets EUR_USD pricing, returns mid
  - Handles cross rates (e.g., GBP/JPY → GBP/USD × USD/JPY)

### 3.4 Enhanced FXRateProvider

#### `CrossRateFXRateProvider` (`domain/fx.py` or `infrastructure/fx_providers/cross_rate.py`)
A composite FX rate provider that chains multiple rate providers to compute
cross rates that no single provider supports directly.

```python
class CrossRateFXRateProvider(FXRateProvider):
    """
    Decorator over one or more FXRateProviders that computes cross rates
    by chaining through USD. E.g., if asked for GBP/CHF but only GBP/USD
    and USD/CHF are available: result = GBP/USD × USD/CHF.
    """
    def __init__(self, providers: List[FXRateProvider]):
        self._providers = providers

    def get_rate(self, from_currency, to_currency, date=None) -> float:
        # Try each provider directly first
        # If none support, try routing through USD:
        #   if from≠USD and to≠USD:
        #     rate = get_rate(from, USD) * get_rate(USD, to)
        #   raise if still not found
```

This is **not** a new concept — it extends the existing `FXRateProvider` ABC
seamlessly. The `App.add_fx_rate_provider()` method already accepts one
provider. The user wraps multiple providers inside `CrossRateFXRateProvider`.

### 3.5 Backtest Engine Enhancements

#### Market Calendar Filter (`domain/backtesting/forex_market.py`)
- New file with filtering logic applied during backtest data preparation.
- The backtest engine already calls `prepare_backtest_data()` → data is loaded
  into an in-memory `pl.DataFrame`.
- After load, apply `ForexMarketCalendar.filter_market_hours(df)` to strip
  weekend candles (when `market="FOREX"` is detected).
- The filter is safe for non-forex data (returns data unchanged if market
  calendar not configured).

#### Pip-Based P&L (`domain/backtesting/pip_pnl.py`)
- New utility that computes P&L in both pips and base currency.
- Used by the backtest engine when `market="FOREX"`.
- Formula:
  ```
  pip_movement = abs(exit_price - entry_price) / pip_size
  pip_pnl = pip_movement * pip_value * lot_size_multiplier
  base_currency_pnl = pip_pnl * quote_to_base_rate
  ```

#### Swap Cost Deduction (`domain/backtesting/swap_tracker.py`)
- New utility that tracks overnight holds and applies swap costs.
- Called during backtest position management:
  - At each day's rollover time (5pm ET), check open positions.
  - If position was open at rollover, apply swap rate.
  - Wednesday → triple swap.
  - Deduct/credit from position P&L.

### 3.6 Order Model Extension

Add `take_profit_price` and `stop_loss_price` fields to the existing `Order`
model. These are optional — used by Oanda for attached TP/SL orders.

### 3.7 Sidecar: Existing Provider Enhancements

#### Alpha Vantage — Forex Dispatch
Modify `AlphaVantageOHLCVDataProvider._download_ohlcv()` to detect forex
symbols (pairs containing `/`) and use `alpha_vantage.foreignexchange.Forex`
instead of `TimeSeries`. The data format is identical after renaming columns.

#### Yahoo — No Change Needed
`YahooOHLCVDataProvider` already supports `EURUSD=X` symbols. Document the
symbol format for users.

#### Polygon — No Change Needed
`PolygonOHLCVDataProvider` already supports `C:EURUSD` symbols. Document.

---

## 4. Data Flow

### Representative Write: Place Oanda Market Order with TP/SL

```
User Strategy
    │
    ▼
app.create_order(symbol="EUR/USD", side="BUY", amount=1.0,
                  order_type="MARKET", take_profit_price=1.11000,
                  stop_loss_price=1.09500)
    │
    ▼
OrderService.create_order(portfolio, order)
    │  (validates: enough margin? pair exists? amount>0?)
    │
    ▼
OrderExecutorLookup.get("OANDA")
    │
    ▼
OandaOrderExecutor.execute_order(portfolio, order, credential)
    │  • Normalize EUR/USD → EUR_USD
    │  • Build Oanda v20 payload:
    │    { "order": {
    │        "type": "MARKET",
    │        "instrument": "EUR_USD",
    │        "units": "10000",
    │        "takeProfitOnFill": { "price": "1.11000" },
    │        "stopLossOnFill": { "price": "1.09500" }
    │    }}
    │  • POST /v3/accounts/{id}/orders
    │  • Handle 429 → retry with backoff
    │  • Handle 5xx → return Order(status=FAILED)
    │
    ▼
Return Order(external_id="1234", status="FILLED",
              filled=10000, price=1.10250)
    │
    ▼
App.state updates:
    • Portfolio position tracked
    • Order stored in DB / in-memory
    • Strategy notified
```

### Representative Read: Backtest OHLCV Data Fetch

```
BacktestEngine.prepare_backtest_data(date_range)
    │
    ▼
For each DataSource:
    DataProviderService.get(data_source)
        │ → FREDOHLCVDataProvider for FRED sources
        │ → TwelveDataOHLCVDataProvider for TWELVEDATA sources
        │ → OandaOHLCVDataProvider for OANDA sources
        │
        ▼
    OHLCVDataProviderBase.prepare_backtest_data(start, end)
        │ • Check CSV cache on disk
        │ • If cached → load pl.DataFrame
        │ • If not cached → _download_ohlcv() → save CSV
        │
        ▼
    If market == "FOREX":
        ForexMarketCalendar.filter_market_hours(df)
            • Remove Sat/Sun candles
            • Log warning if >10% empty (data quality)
        │
        ▼
    Data is now in memory pl.DataFrame, windowed by warmup_window
    Used by backtest engine for per-index-day iteration:
        get_backtest_data(index_date) → sliced DataFrame
```

### Representative Read: Multi-Currency Portfolio Valuation

```
Portfolio.get_net_size()
    │
    ▼
For each position:
    • Position.symbol = "EUR/USD" → base_currency = "EUR"
    • Position.amount = 5000 (EUR)
    │
    ▼
FXRateProvider.get_rate(from_currency="EUR",
                         to_currency="USD")
    │ → OandaFXRateProvider: fetches EUR_USD pricing
    │ → or CrossRateFXRateProvider: chains through USD
    │
    ▼
Return 5000 * 1.10500 = $5,525.00
Sum all positions → total portfolio value in "USD"
```

---

## 5. API Design

### 5.1 Configuration API (User-Facing)

```python
# --- Forex Pair Configuration ---
from investing_algorithm_framework.domain import (
    ForexPairConfiguration, LotSize, ForexMarketCalendar,
)

# Per-pair configuration
app.add_forex_pair_configuration(
    ForexPairConfiguration(
        symbol="EUR/USD",
        pip_decimal_places=4,
        display_decimal_places=5,
        swap_long_rate=Decimal("-0.5"),   # -0.5 pips per lot per day
        swap_short_rate=Decimal("0.3"),   # +0.3 pips per lot per day
        margin_leverage=30,
        default_lot_size=LotSize.MICRO,
    )
)

# --- Data Providers ---
from investing_algorithm_framework.infrastructure import (
    FREDOHLCVDataProvider, TwelveDataOHLCVDataProvider,
    ExchangeRateAPITickerDataProvider,
    OandaOHLCVDataProvider, OandaTickerDataProvider,
)

app.add_data_provider(FREDOHLCVDataProvider(), priority=5)
app.add_data_provider(TwelveDataOHLCVDataProvider(), priority=4)
app.add_data_provider(
    OandaOHLCVDataProvider(
        time_frame="1h", symbol="EUR/USD"
    ), priority=2
)

# --- Market Credentials ---
app.add_market_credential(
    MarketCredential(market="FRED", api_key="...")
)
app.add_market_credential(
    MarketCredential(market="TWELVEDATA", api_key="...")
)
app.add_market_credential(
    MarketCredential(
        market="OANDA",
        api_key="bearer_token",
        secret_key="account_id",  # Oanda account UUID
    )
)

# --- Oanda Live Trading ---
from investing_algorithm_framework.infrastructure import (
    OandaOrderExecutor, OandaPortfolioProvider,
    OandaFXRateProvider,
)

app.add_order_executor(OandaOrderExecutor(priority=1))
app.add_portfolio_provider(OandaPortfolioProvider(priority=1))
app.add_fx_rate_provider(OandaFXRateProvider())

# --- Cross-rate FX Provider ---
from investing_algorithm_framework.domain import CrossRateFXRateProvider

app.add_fx_rate_provider(
    CrossRateFXRateProvider([
        OandaFXRateProvider(),
        StaticFXRateProvider({("USD", "EUR"): 0.92})
    ])
)
```

### 5.2 Order API (Extended)

The existing `Order` model gains two optional fields:

```python
# New fields on Order
order.take_profit_price = 1.11000    # TP level (None if no TP)
order.stop_loss_price = 1.09500     # SL level (None if no SL)

# Existing order creation still works unchanged
order = Order(
    target_symbol="EUR",
    trading_symbol="USD",
    order_type=OrderType.MARKET,
    order_side=OrderSide.BUY,
    amount=10000,           # units of base currency (or lots, see below)
    take_profit_price=1.11000,
    stop_loss_price=1.09500,
)
```

For lot-based sizing, add a `lot_size` field or allow `amount` to accept
`LotSize` values. **Seam:** Create a `LotSizeParameter` type that the order
service resolves to absolute units before passing to the executor. This avoids
changing the `Order` constructor signature in v1 — use a helper:

```python
# Helper — does not change Order constructor
@staticmethod
def Order.from_lots(
    pair: ForexPair,
    lots: Decimal,
    lot_type: LotSize,
    order_type: OrderSide,
    ...
) -> Order:
    units = lots * lot_type.to_units()
    return Order(
        target_symbol=pair.base_currency,
        trading_symbol=pair.quote_currency,
        amount=units,
        ...
    )
```

### 5.3 DataSource (Forex Example)

```python
# FRED daily data
DataSource(
    identifier="eur_usd_fred_1d",
    data_type="OHLCV",
    market="FRED",
    symbol="EUR/USD",
    time_frame="1d",
    warmup_window=200,
)

# Twelve Data hourly
DataSource(
    identifier="eur_usd_twelve_1h",
    data_type="OHLCV",
    market="TWELVEDATA",
    symbol="EUR/USD",
    time_frame="1h",
    warmup_window=500,
)
```

### 5.4 Auth & Credentials

- `OANDA` credentials: `api_key` = Bearer token, `secret_key` = Account ID.
- `FRED` / `TWELVEDATA` / `EXCHANGE_RATE_API`: `api_key` = API key,
  `secret_key` = not used.

### 5.5 Error Handling

All new components follow existing conventions:
- Data provider errors → return empty DataFrame with logged warning (not crash).
- Order executors → return `Order(status=FAILED)` on error (not exception).
- Portfolio providers → return `None` for missing positions (not exception).
- Rate limit (429) → retry with exponential backoff (max 3 retries).

---

## 6. Database Schema

### No new database tables required.

The forex data models (`ForexPair`, `LotSize`, `PipCalculator`, `SwapRate`,
`MarginRequirement`, `ForexMarketCalendar`, `ForexPairConfiguration`) are all
**stateless domain value objects** or **in-memory configurations**. They do
not need SQL persistence.

The existing SQL tables (`SQLOrder`, `SQLPosition`, `SQLPortfolio`, etc.)
work for forex trades because:
- `Order.target_symbol` + `Order.trading_symbol` → "EUR/USD" pair.
- `Position.symbol` → "EUR/USD".
- `Portfolio.trading_symbol` → portfolio base currency ("USD", "EUR").

### Implications
- `Position.amount` stores units of base currency (EUR for EUR/USD).
- For multi-currency portfolios, the `FXRateProvider` aggregates values.
- Swap costs are recorded in `Trade` (P&L attribution) or as part of
  backtest metrics — not as separate database rows.

---

## 7. Caching Strategy

| What | Where | Strategy | TTL | Invalidation |
|------|-------|----------|-----|--------------|
| OHLCV data (FRED, Twelve, Oanda) | Local CSV files | Provider's existing `_save_data_to_storage()` | Permanent (until re-fetched) | Manual re-run or `save=False` |
| Live Oanda pricing | In-memory (OandaFXRateProvider) | Latest-rate cache, per-request | 1–5 seconds | Next request refreshes |
| Oanda account summary | In-memory (portfolio sync) | Cached between sync intervals | configurable (default 60s) | Timer-triggered sync |
| Forex pair metadata | In-memory (ForexPair dict) | Loaded once at app init | Application lifetime | App restart to change |

### Scaling Seam: Redis Cache
If the framework needs to share cached FX rates across processes or reduce
Oanda API calls: wrap `OandaFXRateProvider.get_rate()` with a Redis-backed
read-through cache. This is a **named seam** — not built now, but the
`FXRateProvider` ABC already supports it (no change needed).

---

## 8. Implementation Phases

### Phase 1 — Foundation: Domain Models + Utilities
1. `ForexPair` value object (with symbol normalization)
2. `LotSize` enum
3. `PipCalculator` static utility
4. `SwapRate` data model
5. `MarginRequirement` data model
6. `ForexMarketCalendar` utility
7. `ForexPairConfiguration` config model
8. Order model: add `take_profit_price` and `stop_loss_price` fields
9. `CrossRateFXRateProvider` (enhanced FX rate resolution)

### Phase 2 — Data Providers
1. `FREDOHLCVDataProvider` (daily close only)
2. `TwelveDataOHLCVDataProvider` (true OHLCV, intraday)
3. `ExchangeRateAPITickerDataProvider` (ticker / FX rate)
4. Alpha Vantage: detect forex and dispatch to `Forex` class
5. Yahoo / Polygon: document forex symbol format (no code change)

### Phase 3 — Oanda Live Trading
1. `OandaOHLCVDataProvider`
2. `OandaTickerDataProvider`
3. `OandaFXRateProvider`
4. `OandaOrderExecutor`
5. `OandaPortfolioProvider`

### Phase 4 — Backtest Enhancements
1. Market calendar filter (strip weekends)
2. Pip-based P&L calculation
3. Swap cost deduction per overnight hold

### Phase 5 — Integration & Wiring
1. Register new providers in `infrastructure/__init__.py`
2. Add `get_default_forex_data_providers()` to data_providers `__init__.py`
3. Wire `ForexPairConfiguration` into `App` (add/remove/get methods)
4. Integration tests for each provider
5. Regression tests for backtest engine with forex data

---

## 9. Constitution Check

| Article | Compliant? | Note / justification |
|---------|-----------|----------------------|
| I — Spec before code | ✓ | `spec.md` approved, all `[NEEDS CLARIFICATION]` resolved §Resolved Clarifications |
| II — Minimal but scalable | ✓ | All scaling seams named: Redis cache for FX rates, disk-backed sliding window for backtest. No premature infrastructure. |
| III — Behavior is sacred | ✓ | New feature — no existing behavior changed. (Exception: Alpha Vantage dispatch change preserves behavior for non-forex symbols via normal symbol detection.) |
| IV — Evidence over opinion | ✓ | Provider research in `research.md` documents API behavior, rate limits, and exact code snippets. All technical decisions cite evidence. |
| V — Test-first for critical paths | ✓ | Critical paths: Oanda order execution (rate limit handling, error states), pip P&L calculation (accuracy to 6 decimals), swap cost calculation (Wednesday triple), market calendar filter (weekend edge cases). |
| VI — Security & operability | ✓ | Secrets never in code (existing `MarketCredential` pattern). Input validation at every boundary (symbol normalization, amount > 0). All errors graceful (return None/FAILED, never crash). Logging at every integration point. Oanda 429 handled with backoff. |
| VII — Stay in-session | ✓ | No external LLM orchestration. |
| VIII — Simplicity & reversibility | ✓ | One-way doors assessed: Order model field additions (`take_profit_price`) are backward-compatible (optional, default None). All new provider classes are additive — no existing class modified except Alpha Vantage dispatch (reversible with feature flag). `CrossRateFXRateProvider` is additive. |

**Result: PASS** — all articles compliant.

---

## 10. File-by-File Change List

### New Files to Create

| # | File Path | Purpose |
|---|-----------|---------|
| 1 | `domain/models/forex/__init__.py` | Package init, exports |
| 2 | `domain/models/forex/forex_pair.py` | `ForexPair` value object |
| 3 | `domain/models/forex/lot_size.py` | `LotSize` enum |
| 4 | `domain/models/forex/pip_calculator.py` | `PipCalculator` utility |
| 5 | `domain/models/forex/swap_rate.py` | `SwapRate` data model |
| 6 | `domain/models/forex/margin_requirement.py` | `MarginRequirement` data model |
| 7 | `domain/models/forex/forex_market_calendar.py` | `ForexMarketCalendar` utility |
| 8 | `domain/models/forex/forex_pair_configuration.py` | `ForexPairConfiguration` config model |
| 9 | `domain/fx_providers/__init__.py` | Package init |
| 10 | `domain/fx_providers/cross_rate.py` | `CrossRateFXRateProvider` |
| 11 | `infrastructure/data_providers/fred.py` | `FREDOHLCVDataProvider` |
| 12 | `infrastructure/data_providers/twelve_data.py` | `TwelveDataOHLCVDataProvider` |
| 13 | `infrastructure/data_providers/exchange_rate_api.py` | `ExchangeRateAPITickerDataProvider` |
| 14 | `infrastructure/data_providers/oanda.py` | `OandaOHLCVDataProvider` + `OandaTickerDataProvider` |
| 15 | `infrastructure/fx_providers/__init__.py` | Package init |
| 16 | `infrastructure/fx_providers/oanda_fx_rate_provider.py` | `OandaFXRateProvider` |
| 17 | `infrastructure/order_executors/oanda_order_executor.py` | `OandaOrderExecutor` |
| 18 | `infrastructure/portfolio_providers/oanda_portfolio_provider.py` | `OandaPortfolioProvider` |
| 19 | `domain/backtesting/forex_market.py` | Market calendar filter for backtest engine |
| 20 | `domain/backtesting/pip_pnl.py` | Pip-based P&L calculation |
| 21 | `domain/backtesting/swap_tracker.py` | Swap cost deduction |

### Existing Files to Modify

| # | File | Change |
|---|------|--------|
| 22 | `domain/models/order/order.py` | Add `take_profit_price` and `stop_loss_price` fields (optional, default None) |
| 23 | `infrastructure/data_providers/alpha_vantage.py` | In `_download_ohlcv()`, detect forex symbols and dispatch to `alpha_vantage.foreignexchange.Forex` |
| 24 | `infrastructure/data_providers/__init__.py` | Add new provider imports, add `get_default_forex_data_providers()`, update `__all__` |
| 25 | `infrastructure/order_executors/__init__.py` | Add Oanda order executor, update `__all__` |
| 26 | `infrastructure/portfolio_providers/__init__.py` | Add Oanda portfolio provider, update `__all__` |
| 27 | `infrastructure/__init__.py` | Re-export new infrastructure components |
| 28 | `domain/__init__.py` | Re-export new domain models (`ForexPair`, `LotSize`, etc.) |
| 29 | `app/app.py` | Add `add_forex_pair_configuration()`, `get_forex_pair_configuration()`, `get_forex_pair_configurations()` methods. Wire `ForexPairConfiguration` into portfolio context. |
| 30 | `domain/constants.py` | Add `FOREX_MARKET_IDENTIFIER = "FOREX"` constant (used by market calendar filter) |

### Files Requiring No Change (Document Only)

| File | Note |
|------|------|
| `infrastructure/data_providers/yahoo.py` | Already supports forex (`EURUSD=X`). Document symbol format. |
| `infrastructure/data_providers/polygon.py` | Already supports forex (`C:EURUSD`). Document symbol format. |

---

## 11. Complexity Tracking

No constitutional violations — all 9 articles pass. However, the following
areas carry implementation risk and are flagged for attention:

| Risk Area | Risk Level | Mitigation |
|-----------|------------|------------|
| Oanda API changes | Low | Oanda v20 is stable (launched 2017). Pin `oanda-api-v20` package version. |
| FRED data quality (close-only) | Medium | Document limitation. Users warned that OHLC = all close for FRED. Suggest Twelve Data for true OHLCV. |
| Alpha Vantage forex dispatch | Low | Feature-flag behavior behind symbol presence of `/`. Existing stock symbol behavior unchanged. |
| Cross-rate accuracy | Medium | Cross rates computed by multiplication can accumulate rounding errors. Use `Decimal` throughout for forex pricing. |
| Swap cost Wednesday triple rollover | Medium | Confirm Oanda's rollover timing (5pm ET) is correct given DST transitions. Use UTC-based calculation with configurable rollover hour. |
| Oanda rate limits in practice | Low | 100 req/s for demo accounts is generous for single-user bots. Implement client-side throttling (1 req / 10ms) as safety measure. |
| Timezone handling | Medium | All internal timestamps are UTC. 5pm ET = 22:00 UTC (winter) / 21:00 UTC (summer). Use `pytz` with `US/Eastern` for reliable conversion. |

---

## 12. Test Strategy

### Unit Tests (per component)
- `ForexPair`: symbol normalization, JPY detection, format conversion
- `PipCalculator`: pip value for USD/JPY, EUR/USD, cross pairs
- `SwapRate`: Wednesday triple swap, weekend skip
- `ForexMarketCalendar`: weekend filter, market open check
- `CrossRateFXRateProvider`: direct rate, inverted rate, chained rate, missing pair

### Integration Tests (per provider)
- `FREDOHLCVDataProvider`: mock API response, verify DataFrame schema
- `TwelveDataOHLCVDataProvider`: mock API, verify OHLCV columns
- `ExchangeRateAPITickerDataProvider`: mock API, verify ticker data

### Live / Sandbox Tests
- `OandaOrderExecutor`: against Oanda practice account (demo API key)
- `OandaPortfolioProvider`: against Oanda practice account
- `OandaFXRateProvider`: verify rate against Oanda web dashboard

### Backtest Regression Tests
- Existing non-forex backtest: verify behavior unchanged (Constitution Art. III)
- Forex backtest: pip P&L matches manual calculation
- Swap deduction: verify Wednesday triple swap
- Weekend filter: verify empty Saturday DataFrame

---

## 13. Scaling Playbook (ordered by load growth)

| Trigger | Action |
|---------|--------|
| > 100 API calls/day to Oanda pricing | Add client-side rate limiter (token bucket) to `OandaFXRateProvider` |
| > 5 concurrent strategies needing live FX rates | Enable Redis cache for `OandaFXRateProvider` (seam named above) |
| > 20 data sources in a single backtest | Monitor memory. Seam: disk-backed sliding window in `OHLCVDataProviderBase` |
| > 50k candles loaded per backtest | Move from CSV storage to Parquet (polars-native, faster I/O) |
| Live trading at sub-minute timeframes | Replace OHLCV polling with WebSocket streaming (Oanda v20 supports streaming) |
| Multi-process deployment | Add shared Redis for FX rate cache, ensure stateless order executors |

---

## 14. Failure Modes

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Oanda API unreachable | HTTP timeout / connection error | `OandaOrderExecutor` catches exception, returns `Order(status=FAILED)`. Logged. Framework continues. |
| Oanda 429 rate limit | HTTP 429 + `Retry-After` header | Exponential backoff (1s, 2s, 4s), max 3 retries. Log warning. |
| Provider API key invalid | 401 / 403 response | `MarketCredential.initialize()` catches at startup. Error message identifies which credential. |
| FRED series not found | 400 "series does not exist" | `FREDOHLCVDataProvider` logs error, returns empty DataFrame. Symbol mapping validated at `_validate_symbol()` time. |
| ExchangeRate-API quota exhausted | 429 or 403 | Provider tracks request count in memory, raises `OperationalException` with user-friendly message. |
| Twelve Data quota exhausted | 429 in response header | Same pattern: log, return empty, don't crash. |
| Cross-rate chain not found | No provider supports any intermediate pair | `CrossRateFXRateProvider` raises clear `ValueError` identifying the missing pair (not a generic "rate not found"). |
| Wednesday triple swap mis-timed | DST transition causes 1-hour offset | Rollover time configurable. Document requirement to verify broker rollover schedule. Default: 22:00 UTC. |
| Order submitted seconds before rollover | Oanda may reject or partially fill | `OandaOrderExecutor` handles `PENDING` status gracefully. Next sync resolves. |
