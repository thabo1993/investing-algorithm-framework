# Research — Forex Data Providers & Integration Details

**Feature:** 001-forex-support | **Date:** 2026-07-04

> Researches each free forex data provider, Oanda v20 API capabilities, and
> forex conventions. This resolves the unknowns identified during planning and
> records decisions with rationale.

---

## 1. FRED (Federal Reserve Economic Data)

### Overview
FRED is a database of 800,000+ economic time series maintained by the Federal
Reserve Bank of St. Louis. It publishes daily spot exchange rates for major
currency pairs via its REST API.

### Sign-up & API Key
1. Visit https://fred.stlouisfed.org/docs/api/api_key.html
2. Click "Request an API Key" — registration requires name, email, and intended use.
3. Key is sent via email instantly (automated, no approval delay).
4. **Rate limit:** 120 requests per minute, no daily cap.
5. **Tier:** Entirely free, no paid tier needed.

### Supported Symbols (Forex-relevant series)
FRED uses series IDs, not pair names. Key forex series:

| Series ID | Description |
|-----------|-------------|
| `DEXUSEU` | U.S. Dollars to Euro Spot Rate |
| `DEXJPUS` | Japanese Yen to U.S. Dollars Spot Rate |
| `DEXUSUK` | U.S. Dollars to British Pound Spot Rate |
| `DEXUSAL` | U.S. Dollars to Australian Dollar Spot Rate |
| `DEXUSNZ` | U.S. Dollars to New Zealand Dollar Spot Rate |
| `DEXCAUS` | Canadian Dollars to U.S. Dollars Spot Rate |
| `DEXSZUS` | Swiss Francs to U.S. Dollars Spot Rate |
| `DEXCHUS` | Chinese Yuan to U.S. Dollars Spot Rate |
| `DEXUSBR` | U.S. Dollars to Brazilian Real Spot Rate |
| `DEXUSIN` | U.S. Dollars to Indian Rupee Spot Rate |
| `DEXKOUS` | South Korean Won to U.S. Dollars Spot Rate |
| `DEXMAUS` | Malaysian Ringgit to U.S. Dollars Spot Rate |
| `DEXMXUS` | Mexican Pesos to U.S. Dollars Spot Rate |
| `DEXTAUS` | Taiwanese Dollars to U.S. Dollars Spot Rate |
| `DEXTHUS` | Thai Baht to U.S. Dollars Spot Rate |
| `DEXSFUS` | South African Rand to U.S. Dollars Spot Rate |
| `DEXVZUS` | Venezuelan Bolivares to U.S. Dollars Spot Rate |

### Data Characteristics
- **Type:** Daily close only (not true OHLCV). FRED records a single
  daily observation, typically the noon buying rate.
- **Granularity:** Daily (`"d"` frequency). No intraday data.
- **Date range:** Decades of historical data (many series back to 1970s).
- **Output format:** Observations are date + value pairs via
  `fred/series/observations` endpoint.

### Integration Approach
Create `FREDOHLCVDataProvider` that extends `OHLCVDataProviderBase`:
- Timeframe support: `1d` only (others raise unsupported).
- OHLC columns: Open=Close=High=Low=same observation value (since only one
  rate per day). Volume=0.
- Symbol mapping: Requires a `(pair→series_id)` mapping table. Map
  `EUR/USD` → `DEXUSEU`, `USD/JPY` → `DEXJPUS`, etc.
- API authentication: `MarketCredential(market="FRED", api_key="...")`.

### Working Code Snippet
```python
import requests

API_KEY = "your_fred_api_key"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# EUR/USD: series_id = DEXUSEU
params = {
    "series_id": "DEXUSEU",
    "api_key": API_KEY,
    "file_type": "json",
    "observation_start": "2024-01-01",
    "observation_end": "2024-06-30",
    "sort_order": "asc",
}
resp = requests.get(BASE_URL, params=params)
data = resp.json()

for obs in data["observations"]:
    print(obs["date"], obs["value"])
    # "2024-01-02", "1.1042"
```

### References
- API docs: https://fred.stlouisfed.org/docs/api/fred/
- Series search: https://fred.stlouisfed.org/series/DEXUSEU

---

## 2. ExchangeRate-API

### Overview
ExchangeRate-API provides current and historical exchange rates for 161
currencies. The free tier covers latest rates only (no historical).

### Sign-up & API Key
1. Visit https://www.exchangerate-api.com
2. Click "Get Free API Key" — email registration.
3. Key is available immediately on the dashboard.
4. **Rate limit:** 1,500 requests per month (free tier).
5. **Updated:** Once per day (daily snapshot).
6. **Tiers:** Free → $10/mo (historical) → $30/mo (higher limits).

### Supported Symbols
- All 161 ISO 4217 currencies.
- Pair format: URL-based, e.g., `.../latest/USD` returns all rates from USD.
- No "EUR/USD" as a pair — instead get `EUR` rate from `USD` base.

### Data Characteristics
- **Type:** Latest exchange rate only on free tier (ticker, not OHLCV).
- **Granularity:** Single rate per currency pair, updated daily.
- **Historical:** Paid tier only (via `/history/` endpoint).
- **Output:** JSON with `conversion_rates` object.

### Integration Approach
Create `ExchangeRateAPITickerDataProvider` extending `DataProvider` with
`DataType.TICKER`:
- No OHLCV capability on free tier.
- Act as a ticker data provider for live/latest forex rates.
- Can also serve as an `FXRateProvider` implementation.
- Rate limit awareness: track monthly request count, raise graceful
  `OperationalException` when exhausted.
- API key via `MarketCredential(market="EXCHANGE_RATE_API", api_key="...")`.

### Working Code Snippet
```python
import requests

API_KEY = "your_exchangerate_api_key"
BASE_URL = "https://v6.exchangerate-api.com/v6"

# Get all rates from USD
resp = requests.get(f"{BASE_URL}/{API_KEY}/latest/USD")
data = resp.json()

eur_usd = data["conversion_rates"]["EUR"]  # 1 USD = ? EUR
# For EUR/USD (EUR base): rate = 1.0 / eur_usd
```

### References
- API docs: https://www.exchangerate-api.com/docs
- Pricing: https://www.exchangerate-api.com/pricing

---

## 3. Twelve Data

### Overview
Twelve Data provides real-time and historical OHLCV data for forex, stocks,
crypto, and commodities. Its free tier is generous (800 requests/day) and
supports true OHLCV for forex pairs.

### Sign-up & API Key
1. Visit https://twelvedata.com/apikey
2. Enter email — key sent instantly.
3. **Rate limit:** 800 requests per day (free tier), 8 requests per minute.
4. **Historical depth:** Up to 2 years on free tier (no limit on paid).
5. **Tier:** Free → $19.99/mo (unlimited API calls, 20 yrs history).

### Supported Symbols
- Symbol format: `EUR/USD`, `GBP/JPY`, `USD/CAD`, etc. (uses standard
  slash notation).
- Intraday forex data available.
- All 161 currencies.

### Data Characteristics
- **Type:** True OHLCV (Open, High, Low, Close, Volume).
- **Granularity:** 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week,
  1month.
- **Historical:** Up to 2 years on free tier.
- **Output:** JSON array of OHLCV candles.

### Integration Approach
Create `TwelveDataOHLCVDataProvider` extending `OHLCVDataProviderBase`:
- Full timeframe map (1m through 1M).
- API key via `MarketCredential`.
- Track remaining daily requests from response headers.
- Rate-limit gracefully: return empty DataFrame with logged warning.

### Working Code Snippet
```python
import requests

API_KEY = "your_twelvedata_api_key"
BASE_URL = "https://api.twelvedata.com/time_series"

params = {
    "symbol": "EUR/USD",
    "interval": "1day",
    "apikey": API_KEY,
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "outputsize": "5000",
}
resp = requests.get(BASE_URL, params=params)
data = resp.json()

if data["status"] == "ok":
    for candle in data["values"]:
        print(candle["datetime"], candle["open"], candle["high"],
              candle["low"], candle["close"], candle["volume"])
```

### References
- API docs: https://twelvedata.com/docs
- Playground: https://twelvedata.com/playground

---

## 4. Oanda v20 REST API

### Overview
Oanda's v20 REST API is the industry standard for retail forex automation.
It offers order placement, position management, account details, and pricing
data through a clean REST interface.

### Sign-up & API Key (Demo Account)
1. Visit https://www.oanda.com/demo-account/
2. Register for a "practice" (demo) account — no deposit required.
3. Once registered, generate an API key:
   - Login to https://www.oanda.com/account/access/
   - Navigate to "API Access" or "Manage API Access"
   - Generate a new personal access token (Bearer token).
   - Copy the token immediately (shown once).
4. **Account ID:** Found in the account dashboard. Required in API requests.

### API Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /v3/accounts/{accountID}` | Account details, balance, margin |
| `GET /v3/accounts/{accountID}/summary` | Account summary |
| `GET /v3/accounts/{accountID}/pricing` | Current pricing for instruments |
| `GET /v3/accounts/{accountID}/instruments` | Available instruments |
| `POST /v3/accounts/{accountID}/orders` | Create order |
| `GET /v3/accounts/{accountID}/orders/{orderID}` | Get order |
| `PUT /v3/accounts/{accountID}/orders/{orderID}` | Replace order |
| `PUT /v3/accounts/{accountID}/orders/{orderID}/cancel` | Cancel order |
| `GET /v3/accounts/{accountID}/positions` | List all positions |
| `GET /v3/accounts/{accountID}/positions/{instrument}` | Get position |
| `GET /v3/accounts/{accountID}/trades` | List open trades |
| `GET /v3/accounts/{accountID}/candles` | Get OHLCV candle data |

### Authentication
- **Header:** `Authorization: Bearer <token>`
- **Header:** `Content-Type: application/json`
- All requests include account ID in path.

### Rate Limits
- Practice (demo): 100 requests/second, bursts up to 200.
- Live: 20 requests/second, bursts up to 50.
- `429 Too Many Requests` response has a `Retry-After` header.

### Order Types Supported
| Order Type | v20 Equivalent |
|------------|----------------|
| MARKET | `MARKET` order |
| LIMIT | `LIMIT` order |
| STOP | `STOP` order (entry stop) |
| STOP_LIMIT | `STOP_LIMIT` order (stop with limit) |
| TAKE_PROFIT | `TAKE_PROFIT` order (attached to trade) |
| STOP_LOSS | `STOP_LOSS` order (attached to trade) |
| TRAILING_STOP_LOSS | `TRAILING_STOP_LOSS` order (attached to trade) |

### Pricing Data
- Oanda provides bid/ask/midpoint pricing via the `/pricing` endpoint.
- OHLCV data via `/candles` with granularity: `S5`, `S10`, `S15`, `S30`,
  `M1`, `M2`, `M3`, `M5`, `M10`, `M15`, `M30`, `H1`, `H2`, `H3`, `H4`,
  `H6`, `H8`, `H12`, `D`, `W`, `M`.
- Candles include bid, ask, and midpoint OHLC.

### Working Code Snippet
```python
import requests

API_KEY = "your_oanda_token"
ACCOUNT_ID = "101-001-..."  # from account dashboard
BASE_URL = "https://api-fxpractice.oanda.com"

# Get account summary
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
resp = requests.get(
    f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/summary",
    headers=headers
)
account = resp.json()
print(account["account"]["balance"], account["account"]["marginAvailable"])

# Place a market order
order_payload = {
    "order": {
        "type": "MARKET",
        "instrument": "EUR_USD",
        "units": "10000",  # positive = buy, negative = sell
        "takeProfitOnFill": {"price": "1.11000"},
        "stopLossOnFill": {"price": "1.09500"},
    }
}
resp = requests.post(
    f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/orders",
    headers=headers,
    json=order_payload,
)
order_result = resp.json()
print(order_result["orderCreateTransaction"]["id"])

# Get candles (OHLCV)
params = {
    "granularity": "H1",
    "from": "2024-01-01T00:00:00Z",
    "to": "2024-06-30T00:00:00Z",
}
resp = requests.get(
    f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/candles"
    f"/EUR_USD",
    headers=headers,
    params=params,
)
candles = resp.json()
for candle in candles["candles"]:
    print(candle["time"], candle["mid"]["o"],
          candle["mid"]["h"], candle["mid"]["l"],
          candle["mid"]["c"])
```

### References
- API docs: https://developer.oanda.com/
- v20 REST API spec: https://developer.oanda.com/rest-live-v20/
- Demo registration: https://www.oanda.com/demo-account/

---

## 5. Yahoo Finance (Existing) — Forex Capability

The existing `YahooOHLCVDataProvider` supports forex already. Yahoo Finance
ticker symbols for forex use the format `EURUSD=X`. The existing provider
needs no change — forex symbols just need to be normalized.

### Symbol Format
| Pair | Yahoo Symbol |
|------|-------------|
| EUR/USD | `EURUSD=X` |
| GBP/USD | `GBPUSD=X` |
| USD/JPY | `USDJPY=X` |

### Decision
No new code needed for Yahoo forex. The existing provider already works with
forex symbols — users just configure `symbol="EURUSD=X"` in the DataSource.
However, a `ForexPair` normalizer that converts `EUR/USD` → `EURUSD=X` for
Yahoo (and similar provider-specific formats) should be created as a utility.

---

## 6. Alpha Vantage (Existing) — Forex Capability

Alpha Vantage has dedicated forex API endpoints (`CURRENCY_EXCHANGE_RATE`
for ticker, `FX_INTRADAY` / `FX_DAILY` / `FX_WEEKLY` / `FX_MONTHLY` for
OHLCV). The existing provider uses `get_intraday()` / `get_daily()` which
need to be called with `outputformat` to specify symbol type.

Actually, the Alpha Vantage Python library's `TimeSeries` class also works
with forex symbols — the symbol format `EUR_USD` or `EURUSD` works with
the `FX_*` series functions in the library.

### Decision
The existing `AlphaVantageOHLCVDataProvider` uses the `alpha_vantage` Python
package's `TimeSeries` class. For forex, the `Forex` class from
`alpha_vantage.foreignexchange` should be used instead. Create a separate
`AlphaVantageForexOHLCVDataProvider` or modify existing provider to detect
and handle forex symbols.

**Chosen approach:** Modify `AlphaVantageOHLCVDataProvider._download_ohlcv()`
to detect forex pairs and dispatch to the correct `Forex` API class, since
the data format returned is identical.

---

## 7. Polygon.io (Existing) — Forex Capability

Polygon.io supports forex with the symbol format `C:EURUSD` (the `C:` prefix
denotes currency). The existing provider uses `get_aggs()` which works for
any ticker type. Polygon forex data quality is excellent.

### Decision
The existing `PolygonOHLCVDataProvider` works with forex symbols as-is
when the user configures `symbol="C:EURUSD"`. A `ForexPair` normalizer
can convert `EUR/USD` → `C:EURUSD` for Polygon.

---

## 8. Forex Market Conventions Reference

### Pip Definitions
| Pair Type | Pip Decimal | Display Decimals | Example |
|-----------|-------------|------------------|---------|
| Major pairs (EUR/USD, GBP/USD) | 4th decimal (0.0001) | 5 digits | 1.10500 |
| JPY pairs (USD/JPY, EUR/JPY) | 2nd decimal (0.01) | 3 digits | 154.250 |
| XAU/USD (Gold) | 2nd decimal (0.01) | 2 digits | 1935.50 |

### Pip Values (1 Standard Lot = 100,000 units)
| Pair | Pip Value |
|------|-----------|
| EUR/USD | $10.00 (pip) / $1.00 (pipette) |
| GBP/USD | $10.00 (pip) / $1.00 (pipette) |
| USD/JPY | 1,000 JPY (pip) / 100 JPY (pipette) ≈ $6.45 (varies with rate) |
| EUR/GBP | £10.00 (pip) / £1.00 (pipette) |
| USD/CAD | C$10.00 (pip) / C$1.00 (pipette) |

### Lot Sizes
| Lot Type | Units of Base Currency |
|----------|----------------------|
| Standard | 100,000 |
| Mini | 10,000 |
| Micro | 1,000 |
| Nano | 100 (rare, not commonly used) |

### Market Hours
- **Open:** Sunday 5:00 PM ET (22:00 UTC) — Asia/Pacific session opens.
- **Close:** Friday 5:00 PM ET (21:00 UTC) — US session closes.
- **Trading:** 24 hours/day, 5 days/week.
- **Session overlaps:**
  - Asia: 7:00 PM – 4:00 AM ET (Tokyo dominant)
  - London: 3:00 AM – 12:00 PM ET
  - New York: 8:00 AM – 5:00 PM ET
  - Best overlap: London+NY (8:00 AM – 12:00 PM ET) — highest liquidity

### Rollover / Swap Conventions
- **Time:** 5:00 PM ET (21:00 UTC or 22:00 UTC depending on DST).
- **Wednesday triple swap:** Positions held through Wednesday 5:00 PM ET are
  charged/credited 3× the daily rate (to account for weekend settlement).
- **Swap rates:** Broker-determined based on interbank interest rate
  differentials. Varies by broker and pair.

### Margin / Leverage (Retail)
| Jurisdiction | Max Leverage (Major Pairs) |
|-------------|---------------------------|
| US (NFA) | 1:50 |
| EU (ESMA) | 1:30 |
| UK (FCA) | 1:30 |
| Australia (ASIC) | 1:30 |
| Offshore | Up to 1:500 |

---

## 9. Oanda v20 Symbol Format

Oanda uses underscore-delimited pairs:
| Standard | Oanda Format |
|----------|-------------|
| EUR/USD | `EUR_USD` |
| GBP/JPY | `GBP_JPY` |
| USD/CAD | `USD_CAD` |

The framework must normalize `EUR/USD` → `EUR_USD` for Oanda API calls.
This is handled by the `ForexPair` utility class.

---

## 10. Existing Data Provider Compatibility Matrix

| Provider | OHLCV | Ticker | Forex Native | Needs Change? |
|----------|-------|--------|-------------|---------------|
| Yahoo Finance | ✓ | ✓ | `EURUSD=X` | No (symbol format only) |
| Alpha Vantage | ✓ | ✓ | Via `alpha_vantage.foreignexchange` | Yes (dispatch to Forex class) |
| Polygon.io | ✓ | ✓ | `C:EURUSD` | No (symbol format only) |
| FRED (new) | Partial (close only) | ✗ | Native series IDs | New provider needed |
| ExchangeRate-API (new) | ✗ | ✓ (latest only) | Native | New provider needed |
| Twelve Data (new) | ✓ | ✓ | `EUR/USD` | New provider needed |
| Oanda v20 (new) | ✓ | ✓ | `EUR_USD` | New provider needed (data + exec) |

---

## 11. Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| Default swap cost = 0 | Simplest predictable behavior. Users who care about swaps configure them. |
| JPY pairs display 3 decimals | Modern broker convention; matches Oanda's default display. |
| New `ForexPairConfiguration` model | Clean separation — pair config is neither a MarketCredential nor a DataSource. |
| FRED as `1d` OHLCV (OHLC=close) | FRED only has daily close. Setting OHLC all to same value preserves the 6-column schema while flagging the limitation. |
| ExchangeRate-API as ticker-only provider | Free tier lacks historical. It's useful as a live `FXRateProvider`. |
| Twelve Data as primary free OHLCV provider | True OHLCV, intraday support, generous free tier. |
| Separate `OandaFXRateProvider` | Oanda's pricing API provides the most accurate live rates for portfolio valuation. |
