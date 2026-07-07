# Feature Specification: FOREX Trading Support

**Feature Branch:** `001-forex-support`
**Created:** 2026-07-04
**Status:** Draft
**Input:** User request — add full forex trading support to the investing-algorithm-framework, covering data providers, backtesting rules, live trading via Oanda, forex-specific order types, FX metrics, and multi-currency portfolio valuation.

> Defines the **what** and the **why** — never the *how*. No tech stack, no APIs, no code here.
> That belongs in `plan.md`. Mark every guess or open question with **[NEEDS CLARIFICATION: …]**.

---

### Artifact Naming & Location Conventions

All SDD artifacts for this feature live under `specs/001-forex-support/`:

| Artifact | Path | Phase |
| --- | --- | --- |
| Specification | `specs/001-forex-support/spec.md` | 1 · Specify |
| Design spec | `specs/001-forex-support/design.md` | 1.75 · Design |
| Technical plan | `specs/001-forex-support/plan.md` | 2 · Plan |
| Research notes | `specs/001-forex-support/research.md` | 2 · Plan |
| Data model | `specs/001-forex-support/data-model.md` | 2 · Plan |
| API contracts | `specs/001-forex-support/contracts/*.md` | 2 · Plan |
| Task breakdown | `specs/001-forex-support/tasks.md` | 3 · Tasks |

---

## Executive Summary

The investing-algorithm-framework currently supports **stocks/ETFs** (via Yahoo Finance, Alpha Vantage, Polygon.io) and **crypto** (via CCXT exchange integrations with Binance, Bitvavo, Coinbase). Both asset classes have mature data pipelines, order execution, portfolio providers, and backtesting engines.

**Forex (FX)** is the largest and most liquid financial market in the world, with an average daily trading volume exceeding $7.5 trillion. Adding forex support unlocks an entirely new category of strategies for framework users — from carry trades and trend-following on major pairs (EUR/USD, GBP/USD, USD/JPY) to cross-currency arbitrage and macro models.

Forex differs fundamentally from stocks and crypto in several dimensions that require dedicated support:

- **Market hours:** Forex trades 24 hours a day, 5 days a week (opens Sunday 5pm ET, closes Friday 5pm ET). Backtesting must exclude weekend gaps and handle Monday-open discontinuity.
- **Pricing conventions:** Prices are quoted in pips (4th decimal for most pairs, 2nd for JPY pairs) and pipettes (fractional pips). Lot sizes are standard (100k), mini (10k), and micro (1k) units of base currency.
- **Leverage & margin:** Forex is almost always traded on margin. Position sizing, margin calls, and free margin tracking are essential.
- **Rollover / swap:** Open positions held past 5pm ET incur a rollover credit or debit based on interest rate differentials between the two currencies.
- **Multi-currency portfolios:** A forex portfolio naturally holds positions denominated in different currencies. The framework must convert everything to a single base currency for valuation.
- **Broker APIs:** The major forex brokers (Oanda, FXCM, Interactive Brokers) are not accessible through CCXT, which targets cryptocurrency exchanges. Oanda's v20 REST API is the de-facto standard for retail forex automation and offers free demo accounts.

This feature adds:
1. **Forex data providers** — new providers (FRED, ExchangeRate-API, Twelve Data) plus leverage of existing providers (Yahoo Finance, Alpha Vantage, Polygon) that already support forex symbols.
2. **Forex-aware backtesting** — 24/5 market calendar, pip/pipette conventions, lot sizing, swap cost tracking, and margin modeling.
3. **Live forex trading via Oanda** — a new `OandaOrderExecutor` and `OandaPortfolioProvider` using the v20 REST API.
4. **Forex-specific order management** — Market, Limit, Stop, Stop-Limit, Take-Profit, and Stop-Loss orders integrated with Oanda's native order lifecycle.
5. **FX-specific metrics** — pip-based P&L, swap/rollover cost tracking, margin utilization.
6. **Enhanced multi-currency valuation** — improved `FXRateProvider` support to aggregate positions in different currencies into a single base-currency portfolio value.

---

## User Scenarios & Testing

### User Story 1 — Forex-Data Backtesting (Priority: P1)

As a quantitative trader, I want to backtest a forex trading strategy on major currency pairs using real market data, so that I can evaluate strategy performance under realistic forex market conditions.

**Why this priority:** Without forex data and backtesting rules, no forex strategy can be developed, tested, or validated. Data ingestion and backtesting form the foundational layer that every downstream feature depends on.

**Independent test:** A user can configure a `DataSource` for `EUR/USD` with `market="FOREX"`, run a backtest over a 6-month date range, and receive backtest metrics (total return, Sharpe ratio, max drawdown) that account for 24/5 market hours.

**Acceptance scenarios:**

1. **Given** a configured `DataSource` with symbol `EUR/USD`, market `FOREX`, data type `OHLCV`, and time frame `1h`, **When** the user runs a backtest from 2025-01-01 to 2025-06-30, **Then** the system fetches forex OHLCV data from the highest-priority available provider and the backtest executes successfully with results.

2. **Given** the backtest date range includes weekends (e.g., Saturday or Sunday), **When** the backtest engine processes the data, **Then** it skips weekend timestamps — there are no candles for Saturday or Sunday in the backtest data.

3. **Given** the Monday open follows a weekend gap, **When** the backtest engine computes indicators that depend on prior-day close, **Then** the gap is handled without error (the prior data point is the Friday close; no synthetic data is injected).

4. **Given** a user configures a forex data provider with a free-tier API key (e.g., Alpha Vantage, ExchangeRate-API, FRED), **When** the provider is initialized and `get_data` is called, **Then** the system returns OHLCV data for the requested pair and time range, or raises a clear error if the API limit is reached.

### User Story 2 — Pip-Based Pricing and Lot Sizing (Priority: P1)

As a trader, I want the framework to use forex convention pricing — pips, pipettes, and lot sizes — so that position sizing and P&L calculations match real broker platforms.

**Why this priority:** Pip-based P&L and lot-based position sizing are not cosmetic; they directly affect risk management, stop-loss placement, and backtest fidelity. A strategy optimized without these will produce misleading results.

**Independent test:** A backtest reports position P&L in pips and equivalent base currency, and orders accept size in lots (standard/mini/micro) as well as base-currency units.

**Acceptance scenarios:**

1. **Given** a user configures a position of 1 standard lot on EUR/USD at entry price 1.10500, **When** the price moves to 1.10550 (5 pips), **Then** the P&L is calculated as 5 pips × $10/pip = $50 for a standard lot.

2. **Given** a user places a buy order on USD/JPY with 1 mini lot (10,000 units), **When** the order is executed, **Then** the framework correctly interprets the lot size as 10,000 units of base currency (USD).

3. **Given** the user specifies an order amount in pips for take-profit distance, **When** the order is placed, **Then** the framework converts the pip distance to an absolute price level using the pair's pip value and decimal convention.

4. **Given** the framework displays prices for EUR/USD, **When** outputting price information, **Then** prices are shown to 5 decimal places (e.g., 1.10500) following standard forex convention **[NEEDS CLARIFICATION: Should JPY pairs display 3 decimal places? Most brokers show 3 decimals for JPY pairs — confirm.].**

### User Story 3 — Rollover / Swap Cost Tracking (Priority: P2)

As a forex trader, I want the backtest engine to track daily rollover (swap) costs for positions held overnight, so that strategies like carry trades can be accurately evaluated.

**Why this priority:** Swap costs are a material component of forex returns — especially for longer-term strategies. Ignoring them can dramatically overstate profitability for carry trades or understate it for negative-rollover pairs.

**Independent test:** A backtest on a positive-carry pair (e.g., AUD/JPY in a high-rate environment) shows swap credits accumulating daily, and total return includes both price movement and swap income.

**Acceptance scenarios:**

1. **Given** a long position on AUD/JPY is entered on Monday and held through Friday, **When** the backtest processes each day's rollover at 5pm ET, **Then** the P&L includes a daily swap credit or debit based on the configured interest rate differential.

2. **Given** a position crosses the Wednesday 5pm ET rollover, **When** swap is calculated, **Then** the system applies triple swap (3× the daily rate) to account for weekend settlement conventions.

3. **Given** a user does not configure swap rates for a pair, **When** the backtest encounters an overnight hold, **Then** the system either uses a default swap rate of zero or raises a configurable warning **[NEEDS CLARIFICATION: Should the default be zero swap cost when rates are not configured, or should the system attempt to fetch live swap rates from the data provider / broker?].**

### User Story 4 — Live Forex Trading via Oanda (Priority: P1)

As a trader, I want to connect my Oanda demo account to the framework, so that I can execute forex trades live without manual intervention.

**Why this priority:** Live execution is the end goal of strategy development. Oanda's free demo account makes forex automation accessible to any framework user — no minimum deposit, no credit card required.

**Independent test:** A user configures an Oanda demo account credential, starts the framework in live mode, the framework connects to Oanda's v20 API, and a market order placed via the framework appears in the Oanda web dashboard within 5 seconds.

**Acceptance scenarios:**

1. **Given** a user has configured `MarketCredential(market="OANDA", api_key="...", environment="practice")`, **When** the framework starts in `LIVE` mode, **Then** the OandaOrderExecutor successfully initializes and reports the account's available balance.

2. **Given** the framework is connected to Oanda, **When** a `BUY MARKET` order for 10,000 units of EUR/USD is submitted, **Then** the order is executed on Oanda, an `external_id` is returned, and the order status is reported as `FILLED`.

3. **Given** the framework is connected to Oanda, **When** the `OandaPortfolioProvider.get_position("EUR/USD")` is called, **Then** the current position size and unrealized P&L are returned as reported by Oanda's API.

4. **Given** the Oanda API is unreachable (network failure), **When** an order is submitted, **Then** the executor catches the connection error, sets the order status to `FAILED`, logs the reason, and does not crash the framework.

### User Story 5 — Forex-Specific Order Types with Take-Profit and Stop-Loss (Priority: P2)

As a trader, I want to place orders with attached Take-Profit and Stop-Loss instructions, so that my positions are automatically managed by Oanda's native order book.

**Why this priority:** Attached TP/SL orders are a standard risk-management tool in forex trading and are natively supported by Oanda's API. Implementing them as first-class concepts reduces the burden on the framework's internal order monitoring loop.

**Independent test:** A user places a market buy order for 10,000 EUR/USD with a TP at 50 pips above entry and an SL at 30 pips below entry. The Oanda web dashboard shows all three orders (market + TP + SL) created.

**Acceptance scenarios:**

1. **Given** a user submits a `BUY LIMIT` order for EUR/USD with `take_profit_price=1.11000` and `stop_loss_price=1.10000`, **When** the `OandaOrderExecutor` executes the order, **Then** Oanda creates the limit entry order plus the TP and SL as child orders on Oanda's order book.

2. **Given** an existing open position on GBP/USD, **When** the user adds a trailing stop-loss order, **Then** the framework sends the trailing stop configuration to Oanda's API and the stop updates automatically as price moves.

3. **Given** a take-profit order is triggered (market reaches the TP level), **When** Oanda closes the position, **Then** the framework's next portfolio sync detects the closed position and updates the local state to reflect the completed trade.

### User Story 6 — Multi-Currency Portfolio Valuation (Priority: P2)

As a portfolio manager, I want the framework to value all positions in a single base currency, so that I can assess total portfolio exposure and risk across multiple currency pairs.

**Why this priority:** Forex traders who trade multiple pairs (e.g., EUR/USD, GBP/JPY, USD/CAD) have positions denominated in different currencies. Without multi-currency valuation, the net portfolio value in a trader's base currency (e.g., USD) is unknown, making risk management impossible.

**Independent test:** A portfolio contains positions in EUR/USD (denominated in EUR) and USD/JPY (denominated in USD). The portfolio's `trading_symbol` is set to USD. The `FXRateProvider` fetches a EUR/USD rate, and the total portfolio value is correctly reported in USD.

**Acceptance scenarios:**

1. **Given** a portfolio with `trading_symbol="USD"`, a position in EUR (from a EUR/USD trade worth €5,000), and a position in GBP (from a GBP/USD trade worth £3,000), **When** `portfolio.get_net_size()` is called, **Then** the returned value converts both positions to USD using the configured `FXRateProvider` and returns the sum: `€5,000 * EUR/USD_rate + £3,000 * GBP/USD_rate`.

2. **Given** a portfolio contains a short position (negative amount) in a non-base currency, **When** the total portfolio value is computed, **Then** negative positions are subtracted from the total after currency conversion.

3. **Given** no `FXRateProvider` supports a required conversion (e.g., ZAR/USD not configured), **When** the portfolio valuation is requested, **Then** the system raises a clear error identifying the missing currency pair rather than silently returning an incorrect value.

### User Story 7 — Free Forex Data from Dedicated Providers (Priority: P2)

As a cost-sensitive trader, I want access to free forex data from providers specifically designed for foreign exchange (FRED, ExchangeRate-API, Twelve Data), so that I can choose the best data source for my strategy without paying for data.

**Why this priority:** While Yahoo Finance, Alpha Vantage, and Polygon can supply forex data, dedicated forex/economic data providers like FRED offer additional value (interest rate data for swap calculations, economic indicators for fundamental strategies) that general-purpose providers do not.

**Independent test:** A user configures a `DataSource` pointing to FRED for `EUR/USD` daily data, retrieves 1 year of OHLCV data, and the returned DataFrame has the correct schema and populated values.

**Acceptance scenarios:**

1. **Given** a user configures `FRED` as a data provider with a valid API key, **When** they request OHLCV data for `EUR/USD` with `time_frame="1d"` over 2024, **Then** the system returns a Polars DataFrame with columns `Datetime`, `Open`, `High`, `Low`, `Close`, `Volume` (or equivalent forex-specific columns).

2. **Given** a user configures `ExchangeRate-API` as a data provider, **When** they call `get_data` for a live rate on `GBP/USD`, **Then** the system returns the current exchange rate as a ticker data point.

3. **Given** a user configures `Twelve Data` as a data provider, **When** they request OHLCV data for `USD/JPY` with `time_frame="1h"`, **Then** the system returns the data with proper JPY-pair pricing (3 decimal places for prices).

4. **Given** any of these forex-specific providers exhaust their free-tier rate limits, **When** a data request is made, **Then** the provider returns a graceful error with a message indicating the rate limit has been exceeded, and the framework continues running without crashing.

### User Story 8 — Margin and Leverage Tracking (Priority: P3)

As a risk-conscious trader, I want the framework to track margin utilization and available free margin, so that I avoid over-leveraging my account.

**Why this priority:** Retail forex accounts are typically leveraged 1:30 to 1:500. Without margin tracking, a strategy could unknowingly exceed the broker's margin requirements, resulting in automatic position closures (margin calls).

**Independent test:** A backtest on a 1:30 leverage account with a $10,000 initial balance shows margin utilization percentage as a tracked metric alongside standard backtest metrics.

**Acceptance scenarios:**

1. **Given** a portfolio with `initial_balance=10000` (USD) and leverage of 1:30, **When** a position of 1 standard lot EUR/USD ($100,000 notional) is opened, **Then** the margin utilization is calculated as `$100,000 / 30 / $10,000 = 33.3%` and the free margin is `$10,000 - $3,333.33 = $6,666.67`.

2. **Given** margin utilization exceeds 100%, **When** a new order is submitted, **Then** the framework rejects the order with a `MarginInsufficient` error before sending it to the broker.

3. **Given** a live Oanda account reports margin utilization, **When** the `OandaPortfolioProvider` syncs the portfolio, **Then** the framework updates its local margin utilization and free margin values to match Oanda's reported values.

### Edge Cases

- **Off-market hours (weekends):** Forex data request for Saturday or Sunday returns empty or raises a clear "market closed" error. Backtesting on daily data that spans Monday→Friday only skips weekend dates.
- **Bank holidays / low-liquidity periods:** Some forex pairs have reduced liquidity on certain holidays (e.g., Tokyo closed, London closed). The system SHOULD NOT fabricate data for low-liquidity periods but MAY include a configurable flag to fill missing data.
- **Symbol format variations:** Forex pairs can be expressed as `EUR/USD`, `EURUSD`, `EUR.USD`, or `EUR-USD`. The framework should normalize to `EUR/USD` internally while accepting all common formats at input boundaries.
- **Inverse pairs:** Pairs like USD/CHF and USD/JPY where USD is the base. Pip value calculations must differ from pairs where USD is the quote currency.
- **Exotic pairs:** Emerging-market pairs (USD/ZAR, USD/TRY, USD/BRL) may have wider spreads, fewer data sources, and different liquidity profiles. The data provider resolution should gracefully degrade — if no provider supports an exotic pair, return a clear error.
- **Multiple concurrent forex providers:** When multiple providers support the same symbol, the framework's existing priority mechanism must determine which provider to use, exactly as it works for stocks and crypto today.
- **Oanda API rate limits:** Oanda's API has rate limits (typically 100 requests per second for practice accounts, lower for live). The executor must handle `429 Too Many Requests` with exponential backoff.
- **Order cancellation during rollover:** Oanda processes rollover at 5pm ET. Orders submitted within seconds of rollover may experience unexpected behavior. The framework should handle order status `PENDING` / `TRIGGERED` edge cases gracefully.
- **Partial fills:** Forex market orders on Oanda may be partially filled at multiple price levels if liquidity is insufficient. The `OandaOrderExecutor` must correctly track `filled` vs `remaining` amounts.

---

## Requirements

### Functional Requirements

- **FR-001:** The system MUST support forex market hours — backtesting must exclude weekend (Saturday and Sunday) data and handle Monday-open price gaps without error.
- **FR-002:** The system MUST implement forex pricing conventions: pip (4th decimal for most pairs, 2nd for JPY pairs) and pipette (fractional pip), configurable per pair.
- **FR-003:** The system MUST support forex lot sizes: standard lot (100,000 units), mini lot (10,000 units), and micro lot (1,000 units), with the ability to specify position size in either lots or base-currency units.
- **FR-004:** The system MUST track rollover / swap costs for positions held past 5pm ET, including triple-swap on Wednesday rollovers, with configurable swap rates per pair.
- **FR-005:** The system MUST support leverage and margin calculations, including margin utilization percentage, free margin, and margin call prevention.
- **FR-006:** The system MUST integrate Oanda's v20 REST API for live order execution via a new `OandaOrderExecutor` that implements the `OrderExecutor` abstract base class.
- **FR-007:** The system MUST integrate Oanda's v20 REST API for live portfolio and position management via a new `OandaPortfolioProvider` that implements the `PortfolioProvider` abstract base class.
- **FR-008:** The system MUST support the following order types for forex: Market, Limit, Stop, Stop-Limit, Take-Profit, and Stop-Loss orders. Take-Profit and Stop-Loss MUST be integrated with Oanda's native order management (attached child orders).
- **FR-009:** The system MUST integrate the **FRED API** (Federal Reserve Economic Data) as a forex data provider for OHLCV data.
- **FR-010:** The system MUST integrate **ExchangeRate-API** as a forex data provider (free tier) for live and historical exchange rates.
- **FR-011:** The system MUST integrate **Twelve Data** as a forex data provider (free tier) for OHLCV data.
- **FR-012:** The system MUST leverage existing Yahoo Finance, Alpha Vantage, and Polygon.io providers' existing forex capabilities — these providers already support forex symbols and SHOULD work with forex symbol normalization.
- **FR-013:** The system MUST compute pip-based P&L for forex positions, reporting P&L in both pips and the portfolio's base currency.
- **FR-014:** The system MUST compute and report margin utilization percentage as a tracked metric.
- **FR-015:** The system MUST provide multi-currency portfolio valuation via the existing `FXRateProvider` abstraction, enhanced to handle cross-rate conversions (e.g., converting GBP→USD when only EUR/USD and GBP/EUR rates are available).
- **FR-016:** The system MUST allow users to configure forex-specific parameters per pair: pip decimal places, swap long/short rates, margin requirement percentage, and lot size defaults **[NEEDS CLARIFICATION: Should these be configured as part of MarketCredential, DataSource, or a new ForexPairConfiguration model?].**

### Key Entities

- **ForexPair:** Represents a currency pair (e.g., EUR/USD, GBP/JPY). Attributes include base currency, quote currency, pip decimal places, pip value in quote currency, typical spread, and swap (rollover) rates. This is a logical extension of how the framework currently handles symbols — a forex-specific symbol with additional metadata.
- **Lot:** A unit of position size. Three standard sizes exist: standard (100,000 units of base currency), mini (10,000), and micro (1,000). Users may also specify position size in arbitrary base-currency units.
- **SwapRate:** The overnight rollover cost or credit for holding a position past 5pm ET. Expressed as long rate and short rate per lot, typically in pips or base-currency units per day. Triple swap applies on Wednesday.
- **MarginRequirement:** Defines the percentage of notional value required as margin for a given pair or account. For example, a 1:30 leverage = 3.33% margin requirement. This may be pair-specific or account-wide depending on the broker.
- **PipValue:** The monetary value of one pip movement for a given pair and lot size. This is a derived calculation: pip value depends on the pair (base/quote), lot size, and current exchange rate.

### Non-Functional Requirements

- **NFR-001:** Backtesting performance for forex strategies MUST be comparable to existing stock/crypto backtests on the same hardware and data volume.
- **NFR-002:** Forex data providers that have free-tier API limits (ExchangeRate-API, Twelve Data, Alpha Vantage) MUST handle rate-limit errors gracefully (clear error message, no crash, configurable retry with backoff).
- **NFR-003:** Oanda API outages (HTTP 503, connection refused) MUST NOT crash the framework. The framework SHOULD retry failed requests with configurable backoff (default: 3 retries, exponential backoff).
- **NFR-004:** Pip value and price calculations MUST preserve sufficient precision — a minimum of 6 significant decimal digits for non-JPY pairs and 4 for JPY pairs — to avoid rounding errors in cumulative P&L.
- **NFR-005:** The forex implementation MUST follow the existing framework abstraction patterns (`OHLCVDataProviderBase` for OHLCV data, `OrderExecutor` for order execution, `PortfolioProvider` for portfolio management, `FXRateProvider` for FX rates) and SHOULD NOT introduce parallel abstraction hierarchies.

---

## Success Criteria

Measurable, **technology-agnostic** outcomes that prove the feature works.

- **SC-001:** A user can configure a forex `DataSource`, run a 12-month backtest on EUR/USD at 1h timeframe, and receive complete backtest metrics (total return, Sharpe, max drawdown, trade log) within 2× the time of an equivalent stock backtest on the same hardware.
- **SC-002:** A user can connect to an Oanda demo account, execute a market order, and see the order reflected in the Oanda web dashboard within 10 seconds.
- **SC-003:** A user can configure a multi-currency portfolio (positions in EUR/USD + GBP/USD), set USD as the base currency, and the total portfolio value is correctly computed using live FX rates with < 1% deviation from the equivalent calculation on Oanda's platform.
- **SC-004:** A forex backtest that holds a position for 30 calendar days reports cumulative swap costs within ±5% of a manual calculation using the same swap rates.
- **SC-005:** All 6 forex-specific data providers (FRED, ExchangeRate-API, Twelve Data, Yahoo Finance, Alpha Vantage, Polygon) can be configured and produce valid OHLCV data for at least one major pair on a daily timeframe.
- **SC-006:** Pip-based P&L reported by a live Oanda trade matches the P&L shown in Oanda's web dashboard within ±1 pip.

---

## Out of Scope

The following items are explicitly **out of scope** for this feature. They may be addressed in future features.

- **Non-Oanda live brokers:** FXCM, Interactive Brokers, IG, Saxo Bank, and other forex broker API integrations are out of scope. Oanda is the sole live broker for this feature.
- **Futures / CFDs:** Forex futures (e.g., 6E for EUR/USD futures) and non-forex CFDs (indices, commodities) are out of scope.
- **Tick-level forex data:** This feature covers OHLCV and ticker data. Tick-by-tick forex data is out of scope.
- **Fundamental forex analysis:** Integration of economic calendars, interest rate decisions, or news-based trading is out of scope.
- **Forward points / outright forwards:** This feature covers spot forex only. Forwards, swaps (as derivative contracts), and options are out of scope.
- **GUI / dashboard for forex:** The existing REST API and CLI are sufficient. A dedicated forex trading dashboard is out of scope.
- **Automated swap harvesting:** Strategies that specifically exploit swap rate differentials (swap arbitrage) are a strategy-level concern, not a framework requirement.
- **Correlation / carry matrix analytics:** Multi-pair statistical analysis tools are out of scope.

---

## Assumptions

- **Assumption A1:** Forex pairs follow the ISO 4217 three-letter currency code convention (EUR, USD, JPY, GBP, CHF, CAD, AUD, NZD, etc.) and are quoted as `BASE/QUOTE`.
- **Assumption A2:** The Oanda v20 REST API is sufficient for all live trading use cases (order placement, modification, cancellation, position retrieval, account details). Oanda's API documentation is publicly available and stable.
- **Assumption A3:** Free-tier forex data providers are sufficient for backtesting but may have latency or completeness limitations that make them unsuitable for live ticker data in production. Users who need production-grade live forex data will use Oanda's own data feed or a paid provider.
- **Assumption A4:** The existing `OHLCVDataProviderBase` pattern is extensible enough to support forex OHLCV data providers (FRED, Twelve Data, ExchangeRate-API) without major refactoring.
- **Assumption A5:** The existing `FXRateProvider` abstraction requires enhancement (cross-rate calculation) but not a fundamental redesign to support multi-currency valuation.
- **Assumption A6:** Forex margin requirements are pair-dependent and widely known from broker disclosures. Default margin rates for major pairs will be documented in the feature's user-facing documentation.
- **Assumption A7:** Swap rates change over time. For backtesting, users will provide historical swap rate data or use a configuration-based approach. Live Oanda accounts provide swap rates via the API.
- **Assumption A8:** The framework's existing priority-based data provider resolution mechanism (lower priority number = higher priority) is sufficient for forex and requires no changes.

---

## Review & Acceptance Checklist

- [ ] No implementation detail (stack, APIs, code) has leaked into this spec.
- [ ] Every requirement is testable and unambiguous (no unresolved [NEEDS CLARIFICATION]).
- [ ] Each user story is independently testable and has a clear priority.
- [ ] Success criteria are measurable and technology-agnostic.
- [ ] Scope is bounded — out-of-scope items are listed under Out of Scope.
