# Research: FXCM / ForexConnect capability parity (resolves NC-2 / FR-007)

**Feature:** 002-fxcm-migration
**Date:** 2026-07-05
**Question:** Does Gehtsoft's ForexConnect SDK (`forexconnect`) natively support every
capability the OANDA v20 REST adapter provided? For each: native support (yes/no/partial),
API entry point, source. Anything not confirmable from docs is recorded as a **documented
limitation** and surfaced in `plan.md` — not guessed into existence.

Sources are FXCM/Gehtsoft official docs (fxcodebase.com), the Gehtsoft sample repo, and PyPI.
The SDK **cannot be installed on this repo's Python 3.14 interpreter** (Constraint C1), so every
claim below is doc-derived; runtime verification happens on a supported interpreter under A4.

---

## Session / auth model (foundational — OANDA had none of this)

OANDA authed statelessly per HTTP request (`Authorization: Bearer <api_key>` on a
`requests.Session`). ForexConnect is **stateful and session-oriented**: you open a session,
log in with user/password/host/connection, and the SDK keeps in-memory trading tables live.

```python
from forexconnect import fxcorepy, ForexConnect, Common
with ForexConnect() as fx:
    fx.login("user_id", "password", "fxcorporate.com/Hosts.jsp", "Demo",
             session_status_callback=...)
    ...
    fx.logout()
```

- Entry point: `ForexConnect()` context manager + `ForexConnect.login(user_id, password,
  url, connection)` where `connection` ∈ {`"Demo"`, `"Real"`}.
- This is why FR-010 needs dedicated credential fields (`username`/`password`/`connection`/
  `host_url`) — OANDA's `api_key`/`account_id`/`environment` shape does not map.
- Source: [Getting Price History](https://fxcodebase.com/bin/forexconnect/1.6.0/help/Python/get_history_py.html),
  [MovingAveragesCrossTrading.py](https://github.com/gehtsoft/forex-connect/blob/master/samples/Python/MovingAveragesCrossTrading.py).

---

## Capability parity table

| OANDA capability (adapter had it) | ForexConnect native? | Entry point | Source |
|---|---|---|---|
| Historical OHLCV fetch | **Yes** | `ForexConnect.get_history(instrument, timeframe, date_from, date_to)` | get_history docs |
| Account info / balance | **Yes** | `fx.get_table(ForexConnect.ACCOUNTS)` → rows `account_id`, `balance` | Trading Tables docs |
| Open positions / portfolio | **Yes** | `fx.get_table(ForexConnect.TRADES)` → rows `trade_id`, `instrument`, `amount`, `open_rate` | Trading Tables docs |
| Order placement (market) | **Yes** | `fx.create_order_request(order_type=fxcorepy.Constants.Orders.*, OFFER_ID, ACCOUNT_ID, BUY_SELL, AMOUNT, RATE)` + `fx.send_request(req)` → `resp.order_id` | Creating Order docs |
| Order placement (limit/stop / resting) | **Yes** | `create_order_request` with `order_type=...ENTRY` + `RATE` | Creating Order docs |
| Order status | **Partial** (table, not GET) | `fx.get_table(ForexConnect.ORDERS)` + `Common.subscribe_table_updates(...)`; trades land in TRADES / CLOSED_TRADES | Creating Order / Trading Tables docs |
| Cancel order | **Yes** | `create_order_request` with a delete/cancel order type against the order id | open_position / Creating Order docs |
| Close position | **Yes** | `create_order_request` (true-market close) + `TRADE_ID` | [Opening/Closing Position](https://fxcodebase.com/bin/forexconnect/1.6.0/python/open_position_py.html) |
| TP / SL on fill (OANDA `takeProfitOnFill`/`stopLossOnFill`) | **Partial / unconfirmed** | attached stop/limit orders; single-request parity not confirmed from docs | see limitation L1 |

Historical OHLCV shape from `get_history`: rows expose `Date`, `BidOpen`, `BidHigh`, `BidLow`,
`BidClose`, `Volume` for bar data (`Date`, `Bid`, `Ask` for `"t1"` tick data). Timeframe strings
are `"m1"`, `"H1"`, `"D1"`, etc. Symbols are slash-format (`"EUR/USD"`).
Source: [get_history docs](https://fxcodebase.com/bin/forexconnect/1.6.0/help/Python/get_history_py.html).

---

## Documented limitations (feed FR-007 as limitations, not blockers)

- **L1 — TP/SL attach-on-fill parity unconfirmed.** OANDA attached TP/SL inline in one order
  body (`takeProfitOnFill`/`stopLossOnFill`). ForexConnect's documented model places the primary
  order, then attaches stop/limit orders (often referencing the resulting `trade_id`). The
  create_order_request reference page (fxcodebase 1.6.0) returned 403 to automated fetch, so
  exact single-call TP/SL parameters could not be confirmed from docs. Treat inline TP/SL as a
  **documented limitation**: the FXCM executor accepts TP/SL prices on the `Order` and submits
  them, but exact single-request-vs-secondary-order semantics are verified against the installed
  SDK on a supported interpreter (A4), not asserted here.
- **L2 — Order status is table-driven, not a synchronous GET.** OANDA's portfolio provider did
  `client.get_order(external_id)` (one REST GET) and read `state`. ForexConnect exposes order
  state through in-memory ORDERS / TRADES / CLOSED_TRADES tables, updated via table-listener
  callbacks. The FXCM portfolio provider maps status by reading `get_table(...)` rows for the
  matching order/trade id at call time (no long-lived listener needed for a point-in-time read),
  which is a documented behavioral difference, not a missing capability.
- **L3 — Prices are bid-based and account-specific.** `get_history` returns Bid OHLC (or Bid/Ask
  for ticks) and FXCM notes prices are account-specific; OANDA returned `mid`. The FXCM provider
  maps Bid OHLC → the framework's `Open/High/Low/Close`. Minor numeric difference from OANDA mid,
  documented under NFR-002 (behavior sacred applies *below* the broker boundary, not to the
  broker's own quotes).
- **L4 — Market vs entry order constant + hedging/netting behavior.** The exact `fxcorepy`
  constant for an immediate market order (true-market open) and FXCM's hedging-vs-netting account
  behavior on same-symbol opposite orders are account/config dependent and confirmed only against
  the installed SDK (A4). The executor maps framework `MARKET` → true-market open and
  `LIMIT`/`STOP` → resting `ENTRY`; edge semantics are a documented verification item.
- **L5 — No public backtest archive (already in spec C2, restated).** `get_history` needs a live
  session; `candledata.fxcorporate.com` / github.com/fxcm/MarketData are dead (404). FXCM is a
  live/broker source only.

## Confirmed non-issues

- Symbol format: ForexConnect uses `"EUR/USD"` — identical to the framework's canonical symbol.
  No `to_oanda_format`-style transform is needed; the adapter passes symbols through (uppercased).
- All four surface roles (client/session, OHLCV, order executor, portfolio provider) map onto the
  existing `OHLCVDataProviderBase` / `OrderExecutor` / `PortfolioProvider` base classes (A2) — no
  new abstraction hierarchy (FR-002).

## Sources

- [Getting Price History (get_history)](https://fxcodebase.com/bin/forexconnect/1.6.0/help/Python/get_history_py.html)
- [Creating Order (create_order_request / send_request)](https://fxcodebase.com/bin/forexconnect/1.6.0/python/create_order_py.html)
- [Opening/Closing Position](https://fxcodebase.com/bin/forexconnect/1.6.0/python/open_position_py.html)
- [Getting Data from Trading Tables](https://fxcodebase.com/bin/forexconnect/1.6.0/python/read_table_py.html)
- [Gehtsoft forex-connect samples (Python)](https://github.com/gehtsoft/forex-connect/tree/master/samples/Python)
- [MovingAveragesCrossTrading.py](https://github.com/gehtsoft/forex-connect/blob/master/samples/Python/MovingAveragesCrossTrading.py)
- [forexconnect on PyPI](https://pypi.org/project/forexconnect/) (wheels cp35–37 + one cp310 macOS-ARM, no sdist — confirms C1)
