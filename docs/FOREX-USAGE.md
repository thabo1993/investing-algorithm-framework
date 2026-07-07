# Forex / FX Trading Guide

> Comprehensive guide to forex trading support in the Investing Algorithm Framework.

## Overview

The framework provides end-to-end forex trading support: domain models for pairs and lot sizes, pip-based P&L calculations, swap/rollover cost tracking, margin utilization, a 24/5 market calendar filter for backtesting, and an Oanda integration for live trading.

## Installation

Install optional forex data provider extras:

```bash
pip install investing-algorithm-framework[oanda]       # Oanda live trading
pip install investing-algorithm-framework[fred]         # FRED macroeconomic data
pip install investing-algorithm-framework[twelvedata]    # Twelve Data forex data
```

## How API-Based Data Providers Work

API-based data providers in the framework follow a **two-tier credential system**:

### 1. MarketCredential objects

Every provider that calls an external API needs a `MarketCredential` registered on the app. A credential is a simple object with three fields:

```python
from investing_algorithm_framework.domain import MarketCredential

cred = MarketCredential(
    market="ALPHA_VANTAGE",    # Uppercase market name — must match the provider's `market_name`
    api_key="abc123",          # Your API key
    secret_key=None,           # Optional: some providers (CCXT exchanges) need a secret too
)
```

Credentials are registered on the app:

```python
app.add_market_credential(cred)
# or shorthand:
app.add_market(market="BINANCE", api_key="...", secret_key="...")
```

### 2. Environment variable fallback

If you omit `api_key` (or `secret_key`) when constructing a `MarketCredential`, the framework falls back to the **environment variable** `{MARKET}_API_KEY` (and `{MARKET}_SECRET_KEY`) at initialization time. This is handled by `MarketCredential.initialize()` in `domain/models/market/market_credential.py:21-59`.

```bash
# .env file or export in shell
ALPHA_VANTAGE_API_KEY=abc123
POLYGON_API_KEY=poly_xyz
FRED_API_KEY=fred_xyz
TWELVEDATA_API_KEY=twelve_xyz
OANDA_API_KEY=oanda_abc
OANDA_ACCOUNT_ID=123-456
BINANCE_API_KEY=binance_key
BINANCE_SECRET_KEY=binance_secret
```

### 3. Provider credential lookup

There are two code paths for providers to retrieve their credentials:

| Base Class | Method | Used By |
|------------|--------|---------|
| `OHLCVDataProviderBase` | `_get_api_key()` | Alpha Vantage, Polygon, FRED, Twelve Data |
| `DataProvider` | `get_credential(market)` | CCXT, ExchangeRate-API |

Both methods internally look up the credential that was registered via `app.add_market_credential()` or the environment variable fallback.

### 4. .env file setup

The framework calls `load_dotenv()` automatically when using `create_app()` (`infrastructure/create_app.py:32`), or you can call it manually:

```python
from dotenv import load_dotenv
load_dotenv()  # loads .env from the current directory
```

Create a `.env` file in your project root (it's in `.gitignore` by default):

```bash
# .env — never commit this file
ALPHA_VANTAGE_API_KEY=your_key_here
OANDA_API_KEY=your_key_here
OANDA_ACCOUNT_ID=your_account_id
```

Or run the scaffold command to generate a template:

```bash
investing-algorithm-framework init
# creates .env.example in your project — copy it to .env and fill in values
```

### 5. Quick reference: Market -> env var -> credential name

| Provider | Market Name | Env Var(s) | Required |
|----------|-------------|------------|----------|
| Alpha Vantage | `ALPHA_VANTAGE` | `ALPHA_VANTAGE_API_KEY` | Yes |
| Polygon | `POLYGON` | `POLYGON_API_KEY` | Yes |
| FRED | `FRED` | `FRED_API_KEY` | Yes |
| Twelve Data | `TWELVEDATA` | `TWELVEDATA_API_KEY` | Yes |
| ExchangeRate-API | `EXCHANGERATE_API` | `EXCHANGERATE_API_API_KEY` | Yes |
| Oanda | `OANDA` | `OANDA_API_KEY` | Yes |
| Yahoo Finance | `YAHOO` | *(none — free, no key)* | No |
| CCXT (Binance, etc.) | e.g. `BINANCE` | `{EXCHANGE}_API_KEY`, `{EXCHANGE}_SECRET_KEY` | Yes |

---

## Getting API Keys for Each Provider

### Oanda (Live Forex Trading)

Oanda provides a REST API for forex trading with practice (demo) and live environments.

**Steps:**
1. Go to [https://www.oanda.com](https://www.oanda.com) and create an account
2. For a demo account, sign up at [https://www.oanda.com/demo-account/](https://www.oanda.com/demo-account/)
3. Once logged in, go to **Manage API Access** (under your profile/account settings)
4. Click **Generate API Key**
5. Copy the API key and note your Account ID (shown on the account summary page)

**Environment variables:**
```bash
OANDA_API_KEY=your-40-character-api-key
OANDA_ACCOUNT_ID=your-account-id    # format: 123-456-7890123-001
OANDA_ENVIRONMENT=practice          # "practice" (default) or "live"
```

**Notes:**
- The **practice** environment uses `https://api-fxpractice.oanda.com`
- The **live** environment uses `https://api-fxtrade.oanda.com`
- Always start with practice/demo before going live

### Alpha Vantage (Free FX Data)

Alpha Vantage offers free forex and crypto OHLCV data via REST API.

**Steps:**
1. Go to [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
2. Enter your email and click **Get Free API Key**
3. The key is emailed to you immediately — it's a string like `ABCD1234`
4. Free tier: 5 API calls per minute, 500 per day

**Environment variable:**
```bash
ALPHA_VANTAGE_API_KEY=ABCD1234
```

**Notes:**
- Free tier has rate limits (5 req/min). For backtesting, this means data may load slowly.
- For higher limits, paid plans are available.
- The provider dispatches `EUR/USD`-style symbols to the `CURRENCY_EXCHANGE_RATE` endpoint and plain symbols to `TIME_SERIES_*`.

### Polygon (US Equities & FX)

Polygon provides real-time and historical market data, including forex pairs.

**Steps:**
1. Go to [https://polygon.io/](https://polygon.io/)
2. Click **Get Started** or **Sign Up**
3. Choose a plan (free tier available with delayed data)
4. After signing up, find your API key in the **Dashboard** → **API Keys**
5. Free tier: 5 API calls per minute

**Environment variable:**
```bash
POLYGON_API_KEY=poly_abc123def456
```

**Notes:**
- Forex pairs use the format "EURUSD" (no slash, no underscore)
- Free tier has significant rate restrictions

### FRED (Federal Reserve Economic Data)

FRED provides macroeconomic data (interest rates, GDP, inflation) that can be used as features in forex strategies.

**Steps:**
1. Go to [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Click **Request an API Key**
3. Fill in the form (name, email, intended use)
4. The key is emailed to you instantly
5. Also browse [https://fred.stlouisfed.org/series](https://fred.stlouisfed.org/series) to find series IDs (e.g., `FEDFUNDS` for Fed Funds Rate, `DTWEXBGS` for trade-weighted USD)

**Environment variable:**
```bash
FRED_API_KEY=abcdefghijklmnopqrstuvwxyz1234
```

**Example usage:**
```python
from investing_algorithm_framework.infrastructure.data_providers import FREDOHLCVDataProvider

provider = FREDOHLCVDataProvider(api_key="your-key")
# Or via MarketCredential:
app.add_market_credential(
    MarketCredential(market="FRED", api_key="your-key")
)
```

**Notes:**
- FRED data is **not** live forex prices — it's macroeconomic indicators
- Use it as a supplemental data source for fundamental signals
- Rate limit: 120 requests per minute (free tier)

### Twelve Data

Twelve Data provides real-time and historical forex, crypto, and stock data.

**Steps:**
1. Go to [https://twelvedata.com/](https://twelvedata.com/)
2. Click **Sign Up** (email or Google/GitHub login)
3. After logging in, find your API key in the **Dashboard** → **API Keys**
4. Free tier: 800 API calls per day, 8 calls per minute

**Environment variable:**
```bash
TWELVEDATA_API_KEY=your-twelve-data-key
```

**Notes:**
- Supports forex pairs via `EUR/USD` format
- Free tier is limited — suitable for testing but not production
- Paid plans available for higher limits

### ExchangeRate-API

ExchangeRate-API provides currency conversion rates (not OHLCV, but spot rates for portfolio conversion).

**Steps:**
1. Go to [https://www.exchangerate-api.com/](https://www.exchangerate-api.com/)
2. Click **Get Free API Key**
3. Enter your email and the key is sent to you
4. Free tier: 1,500 requests per month

**Environment variable:**
```bash
EXCHANGERATE_API_API_KEY=your-exchangerate-api-key
```

**Notes:**
- This provider is for **currency conversion rates**, not historical OHLCV data
- Used internally by the FX conversion system (`context.convert_to_base_currency()`)
- Free tier is limited but sufficient for personal use

### Yahoo Finance (Free, No Key)

Yahoo Finance is available through the `yfinance` library and requires **no API key**. It is used for stocks, ETFs, and crypto — not forex pairs. The `YahooOHLCVDataProvider` is available without any credential setup.

---

## Core Domain Models

All forex models live in `investing_algorithm_framework.domain.models.forex`.

### ForexPair

Represents a currency pair (e.g. EUR/USD). Parses symbols in multiple formats:

```python
from investing_algorithm_framework.domain.models.forex import ForexPair

pair = ForexPair.from_symbol("EUR/USD")
pair.base      # "EUR"
pair.quote     # "USD"

# Alternative formats
ForexPair.from_symbol("GBPUSD")       # without slash
ForexPair.from_symbol("EUR_USD")      # Oanda format
ForexPair.from_symbol("EUR-USD")      # Yahoo finance format

# Properties
pair.is_jpy_pair()                    # True for USD/JPY, EUR/JPY etc.
pair.pip_decimal_places               # 4 for non-JPY, 2 for JPY
pair.display_decimal_places           # 5 for non-JPY, 3 for JPY
pair.inverse_pair()                   # USD/EUR
pair.to_oanda_format()                # "EUR_USD"
pair.to_yahoo_format()                # "EURUSD=X"
pair.to_polygon_format()              # "EURUSD"
```

### LotSize

Standard, mini, and micro lot sizes:

```python
from investing_algorithm_framework.domain.models.forex import LotSize

LotSize.STANDARD                      # 100,000 units
LotSize.MINI                          # 10,000 units
LotSize.MICRO                         # 1,000 units

LotSize.from_units(10000)             # LotSize.MINI
LotSize.STANDARD.to_decimal()          # Decimal('100000')
```

### PipCalculator

Converts between prices and pips, and calculates pip values:

```python
from investing_algorithm_framework.domain.models.forex import (
    ForexPair, LotSize, PipCalculator,
)

pair = ForexPair.from_symbol("EUR/USD")

# Price difference to pips
PipCalculator.price_to_pips(
    pair, Decimal("1.1000"), Decimal("1.1050")
)  # 50.00

# Pips to price target
PipCalculator.pips_to_price(
    pair, Decimal("1.1000"), Decimal("50")
)  # 1.1050

# Pip value in quote currency
PipCalculator.pip_value(
    pair=pair, units=LotSize.MINI,
)  # 1.0 (10,000 × 0.0001)

# Full P&L
PipCalculator.calculate_pnl(
    pair=pair,
    entry_price=Decimal("1.1000"),
    exit_price=Decimal("1.1050"),
    units=LotSize.MINI,
)
# {'pips': 50.00, 'pip_value': 1.0, 'pip_pnl_in_quote': 50.0, 'pip_pnl_in_base': 50.0}
```

### SwapRate

Overnight rollover costs:

```python
from investing_algorithm_framework.domain.models.forex import (
    ForexPair, SwapRate,
)
from investing_algorithm_framework.domain.models.order.order_side import OrderSide

pair = ForexPair.from_symbol("EUR/USD")
swap = SwapRate(pair=pair, long_rate=Decimal("-3.5"), short_rate=Decimal("1.2"))

# Calculate swap cost for holding 0.1 lots long for 1 day
swap.calculate_swap(side=OrderSide.BUY, units=Decimal("10000"), days_held=1)
```

### MarginRequirement

Margin based on leverage:

```python
from investing_algorithm_framework.domain.models.forex import (
    ForexPair, MarginRequirement,
)

pair = ForexPair.from_symbol("EUR/USD")
margin_req = MarginRequirement(pair=pair, leverage=30)
margin_req.required_margin(Decimal("100000"))  # 3333.33
```

## Backtesting Enhancements (Phase 4)

Four modules extend the backtesting engine for forex-specific calculations.

### Market Calendar Filter

The forex market runs 24/5 (opens Sunday 21:00 UTC, closes Friday 21:00 UTC). The calendar filter strips weekend data before backtesting:

```python
from investing_algorithm_framework.domain.backtesting import apply_market_calendar_filter
import polars as pl

df = pl.DataFrame({
    "Datetime": [saturday, monday],
    "close": [1.0, 1.1],
})

filtered = apply_market_calendar_filter(
    df, market="FOREX", datetime_column="Datetime"
)
# Saturday row removed
```

### Pip P&L

Scored `PipPnLResult` with direction-aware pip and base-currency P&L:

```python
from investing_algorithm_framework.domain.backtesting import calculate_pip_pnl
from investing_algorithm_framework.domain.models.forex import ForexPair

pair = ForexPair.from_symbol("EUR/USD")
result = calculate_pip_pnl(
    entry_price=Decimal("1.1000"),
    exit_price=Decimal("1.1050"),
    pair=pair,
    units=Decimal("10000"),
)
result.pips               # 50.00
result.pip_value_in_quote # 1.0
result.base_currency_pnl  # 50.00
```

Negative when exit < entry (price moved against a long position):

```python
result = calculate_pip_pnl(
    entry_price=Decimal("1.1050"),
    exit_price=Decimal("1.1000"),
    pair=pair,
    units=Decimal("10000"),
)
result.pips               # -50.00
result.base_currency_pnl  # -50.00
```

For cross-currency conversions, provide `quote_to_base_rate`:

```python
result = calculate_pip_pnl(
    entry_price=Decimal("1.1000"),
    exit_price=Decimal("1.1050"),
    pair=pair,
    units=Decimal("10000"),
    quote_to_base_rate=Decimal("0.85"),
)
```

### Swap Tracker

Tracks cumulative swap costs across positions during backtesting:

```python
from investing_algorithm_framework.domain.backtesting import SwapTracker
from investing_algorithm_framework.domain.models.forex import (
    ForexPair, SwapRate,
)

tracker = SwapTracker()
tracker.configure(
    ForexPair.from_symbol("EUR/USD"),
    SwapRate(long_rate=Decimal("-3.5"), short_rate=Decimal("1.2")),
)

# Check overnight swap for a long position held through rollover
tracker.calculate_rollover_swap(
    pair=ForexPair.from_symbol("EUR/USD"),
    side="long",
    units=Decimal("10000"),
    position_held_at_rollover=True,
)

# Total swap cost over a date range
tracker.calculate_swap_for_date_range(
    pair=ForexPair.from_symbol("EUR/USD"),
    side="long",
    units=Decimal("10000"),
    entry_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    exit_date=datetime(2024, 1, 5, tzinfo=timezone.utc),
)
```

The `side` parameter accepts both strings (`"long"`/`"short"`) and `OrderSide` enum values.

### Margin Utilization

Compute margin usage and detect margin calls:

```python
from investing_algorithm_framework.domain.backtesting import (
    calculate_margin_utilization,
)

result = calculate_margin_utilization(
    position_notional=Decimal("100000"),
    account_balance=Decimal("10000"),
    leverage=30,
)
result.margin_used            # 3333.33
result.margin_available       # 6666.67
result.utilization_percentage # 33.33
result.is_margin_call         # False
result.leverage               # 30
```

A margin call is triggered when `margin_used >= account_balance` (and balance > 0).

## Oanda Live Trading Integration

Oanda integration is available when you install the `oanda` extra:

```bash
pip install investing-algorithm-framework[oanda]
```

### Credential Setup

Register an Oanda credential on the app. The framework looks for `OANDA_API_KEY` and falls back to the environment variable if not provided explicitly:

```python
from investing_algorithm_framework.domain import MarketCredential

app.add_market_credential(
    MarketCredential(market="OANDA", api_key="your-api-key")
)
```

Or via `.env` file:

```bash
OANDA_API_KEY=your-40-character-api-key
OANDA_ACCOUNT_ID=123-456-7890123-001
OANDA_ENVIRONMENT=practice
```

### OandaOHLCVDataProvider

Fetches OHLCV data from Oanda's REST API. Credentials are resolved from the registered `MarketCredential` at runtime:

```python
from investing_algorithm_framework.infrastructure import OandaOHLCVDataProvider

provider = OandaOHLCVDataProvider(
    api_key="your-api-key",
    environment="practice",  # or "live"
)
```

### OandaOrderExecutor

Places market and limit orders on Oanda:

```python
from investing_algorithm_framework.infrastructure import OandaOrderExecutor

executor = OandaOrderExecutor(
    api_key="your-api-key",
    account_id="your-account-id",
    environment="practice",
)
```

### OandaPortfolioProvider

Syncs portfolio state (positions, balances) from Oanda:

```python
from investing_algorithm_framework.infrastructure import OandaPortfolioProvider

provider = OandaPortfolioProvider(
    api_key="your-api-key",
    account_id="your-account-id",
    environment="practice",
)
```

### Complete Oanda wiring

```python
from investing_algorithm_framework import create_app
from investing_algorithm_framework.domain import MarketCredential
from investing_algorithm_framework.infrastructure import (
    OandaOHLCVDataProvider,
    OandaOrderExecutor,
    OandaPortfolioProvider,
)

app = create_app()

# Credential (or rely on OANDA_API_KEY env var)
app.add_market_credential(
    MarketCredential(market="OANDA", api_key="your-key")
)

# Data provider
app.add_data_provider(OandaOHLCVDataProvider())
app.add_order_executor(OandaOrderExecutor(account_id="123-456"))
app.add_portfolio_provider(OandaPortfolioProvider(account_id="123-456"))
```

## Wiring into the App

Register forex pair configuration and Oanda components on the app:

```python
from investing_algorithm_framework import App
from investing_algorithm_framework.domain.models.forex import (
    ForexPairConfiguration,
)

app = App(name="forex_bot")

# Using a ForexPairConfiguration object
app.add_forex_pair_configuration(
    ForexPairConfiguration(
        symbol="EUR/USD",
        swap_long_rate=Decimal("-3.5"),
        swap_short_rate=Decimal("1.2"),
        margin_leverage=30,
        default_lot_size=LotSize.MICRO,
    )
)

# Or using keyword arguments
app.add_forex_pair_configuration(
    symbol="GBP/USD",
    swap_long_rate=Decimal("-2.1"),
    swap_short_rate=Decimal("0.8"),
)
```

## End-to-End Example

See `examples/forex/forex_strategy.py` for a complete EUR/USD SMA crossover strategy:

- Defines `ForexSmaCrossover` strategy with H1 data
- Uses `apply_market_calendar_filter` to restrict trading to forex market hours
- Enters long on SMA crossover, exits on crossunder
- Computes pip-based P&L on exit
- Checks margin utilization before entering positions
- Configurable for both backtesting and Oanda live trading

```python
# Backtest mode (no API keys needed)
python examples/forex/forex_strategy.py

# Live mode (requires OANDA_API_KEY, OANDA_ACCOUNT_ID env vars)
OANDA_API_KEY=... OANDA_ACCOUNT_ID=... python examples/forex/forex_strategy.py
```

## Data Providers

Forex-specific data providers (all optional — install extras as needed):

| Provider | Class | Extra | Source |
|----------|-------|-------|--------|
| Oanda | `OandaOHLCVDataProvider` | `oanda` | Oanda REST API |
| FRED | `FREDOHLCVDataProvider` | `fred` | FRED macroeconomic data |
| Twelve Data | `TwelveDataOHLCVDataProvider` | `twelvedata` | Twelve Data |
| ExchangeRate-API | `ExchangeRateAPITickerDataProvider` | `exchange_rate_api` | exchangerate-api.com |

## API Reference

### Domain Models (`domain.models.forex`)

- `ForexPair` — currency pair representation
- `LotSize` — STANDARD / MINI / MICRO lot sizes
- `PipCalculator` — pip ↔ price conversion, pip value, P&L
- `SwapRate` — overnight rollover rates
- `MarginRequirement` — leverage-based margin
- `ForexMarketCalendar` — 24/5 market hours
- `ForexPairConfiguration` — per-pair settings

### Backtesting (`domain.backtesting`)

- `calculate_pip_pnl()` → `PipPnLResult`
- `SwapTracker` — configurable rollover cost tracker
- `calculate_margin_utilization()` → `MarginUtilizationResult`
- `apply_market_calendar_filter()` — strips weekend data

### Infrastructure (`infrastructure.oanda`)

- `OandaClient` — low-level Oanda REST client
- `OandaOHLCVDataProvider` — OHLCV data provider
- `OandaOrderExecutor` — order execution
- `OandaPortfolioProvider` — portfolio sync

### Infrastructure Data Providers (`infrastructure.data_providers`)

- `FREDOHLCVDataProvider`
- `TwelveDataOHLCVDataProvider`
- `ExchangeRateAPITickerDataProvider`
