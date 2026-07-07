# Implementation Plan: FXCM Migration (replace OANDA)

**Feature:** 002-fxcm-migration
**Date:** 2026-07-05
**Input:** `spec.md` (all Open Questions resolved 2026-07-05), `research.md` (NC-2 / FR-007).
**Mode:** Ponytail / minimal viable. This is a like-for-like adapter swap, not a redesign.
Deliberate shortcuts are marked `ponytail:` in code.

Binding decisions (final, not reopened): full OANDA deletion; FXCM mirrors the 4-part surface;
lazy-optional `forexconnect`; dedicated FXCM credential fields; ForexPair OANDA helpers removed;
FXCM is not a backtest source.

---

## 1. Architecture delta (file-by-file)

### Deleted
- `investing_algorithm_framework/infrastructure/oanda/` (whole package):
  `__init__.py`, `oanda_client.py`, `oanda_data_provider.py`, `oanda_order_executor.py`,
  `oanda_portfolio_provider.py`.
- `tests/infrastructure/test_oanda.py` (replaced by `test_fxcm.py`).

### Created
- `investing_algorithm_framework/infrastructure/fxcm/__init__.py` — exports the 4 classes
  (mirror of the OANDA package `__init__.py`).
- `.../fxcm/fxcm_client.py` — `FxcmClient` + the single lazy-import helper `_load_forexconnect()`.
- `.../fxcm/fxcm_data_provider.py` — `FxcmOHLCVDataProvider(OHLCVDataProviderBase)`.
- `.../fxcm/fxcm_order_executor.py` — `FxcmOrderExecutor(OrderExecutor)`.
- `.../fxcm/fxcm_portfolio_provider.py` — `FxcmPortfolioProvider(PortfolioProvider)`.
- `investing_algorithm_framework/domain/models/market/fxcm_credential.py` —
  `FxcmCredential(MarketCredential)` (see §2).
- `tests/infrastructure/test_fxcm.py` — mocks the SDK boundary (mirror of test_oanda.py).

### Edited
- `investing_algorithm_framework/infrastructure/__init__.py` — replace the two OANDA import
  lines (23–24) and the four `__all__` entries (68–71) with the FXCM equivalents. Placement is a
  direct mirror; nothing else in this file changes.
- `investing_algorithm_framework/domain/models/forex/forex_pair.py` — delete
  `to_oanda_format()` (lines 31–32) and `from_oanda_format()` (34–36). Nothing else touched;
  base/quote parsing and Yahoo/Polygon helpers stay (FR-009 / A3).
- `investing_algorithm_framework/domain/models/market/__init__.py` — export `FxcmCredential`
  alongside `MarketCredential` (only if `MarketCredential` is re-exported there; verify at impl).
- `pyproject.toml` — replace `oanda = []` extra with `fxcm = ["forexconnect"]`; add
  `forexconnect` as an **optional** dependency entry (§5).
- `docs/FOREX-USAGE.md`, `examples/forex/forex_strategy.py`, `README.md` — OANDA → FXCM (§8).
- `tests/domain/test_forex_models.py` — delete `test_to_oanda_format` / `test_from_oanda_format`
  (lines 46–51).

### Component diagram (unchanged shape; broker box swapped)

```
Strategy / App
      │  (add_data_provider / add_order_executor / add_portfolio_provider,
      │   add_market_credential(FxcmCredential))
      ▼
infrastructure.fxcm
 ┌─────────────────────────────────────────────────────────────┐
 │ FxcmOHLCVDataProvider   FxcmOrderExecutor   FxcmPortfolioProvider │
 │        │                     │                     │          │
 │        └─────────────┬───────┴──────────┬──────────┘          │
 │                      ▼                  ▼                      │
 │                 FxcmClient  ── _load_forexconnect() (lazy) ──▶ forexconnect SDK
 │                      │                                (import at connect-time only)
 └──────────────────────┼──────────────────────────────────────┘
                        ▼
              FXCM live session (ForexConnect().login(Demo|Real))
```

State owner: `FxcmClient` owns the live ForexConnect session. The three providers are stateless
w.r.t. the SDK — each builds a client from the credential when it needs a live call. Scaling axis
is N/A (single-user broker adapter); the seam for connection reuse is named in §9.

---

## 2. Credential design (FR-010, resolves NC-1)

Least-code path that keeps existing credential plumbing working: **subclass `MarketCredential`.**
The app looks up credentials by `.market` attribute (`DataProvider.get_credential(market)` iterates
`market_credentials` matching `credential.market`), so a subclass with `market == "FXCM"` is found
by the existing lookup unchanged.

`investing_algorithm_framework/domain/models/market/fxcm_credential.py`:

```python
class FxcmCredential(MarketCredential):
    def __init__(self, username=None, password=None,
                 connection="Demo", host_url=None, market="FXCM"):
        super().__init__(market=market)      # api_key/secret_key stay None, unused
        self._username = username
        self._password = password
        self._connection = connection        # "Demo" | "Real"
        self._host_url = host_url

    def initialize(self):
        # ponytail: dedicated FXCM env vars; override base initialize() which
        # requires api_key. FXCM auth needs username/password/connection/host_url.
        self._username = self._username or os.getenv("FXCM_USERNAME")
        self._password = self._password or os.getenv("FXCM_PASSWORD")
        self._connection = os.getenv("FXCM_CONNECTION", self._connection)
        self._host_url = self._host_url or os.getenv("FXCM_URL")
        if not self._username or not self._password:
            raise OperationalException(
                "FXCM credential requires a username and password, either as "
                "arguments or as FXCM_USERNAME / FXCM_PASSWORD environment "
                "variables (connection: FXCM_CONNECTION, host: FXCM_URL)."
            )
    # + username/password/connection/host_url read-only properties
```

Rationale: subclass over a new field-set on `MarketCredential` — zero change to the base model
(NFR-002: non-FXCM credential behavior identical), and the base's list-based lookup is reused
verbatim. `host_url` may be `None` at construct time; the client falls back to the SDK's default
FXCM host when unset. Env-var names exactly per FR-010: `FXCM_USERNAME`, `FXCM_PASSWORD`,
`FXCM_CONNECTION`, `FXCM_URL`.

---

## 3. Lazy-import mechanism (FR-004, FR-006, US3)

One helper, in `fxcm_client.py`, called only inside `FxcmClient.connect()` (never at module load):

```python
def _load_forexconnect():
    try:
        from forexconnect import fxcorepy, ForexConnect, Common
    except ImportError as e:
        raise OperationalException(
            "Live FXCM trading requires the 'forexconnect' package, which is "
            "not installed. Install it with: "
            "pip install investing-algorithm-framework[fxcm]. Note: forexconnect "
            "ships wheels only for CPython 3.5-3.7 (plus one 3.10 macOS-ARM build) "
            "and cannot be installed on Python 3.14 or most modern interpreters; "
            "run live FXCM strategies on a supported interpreter (e.g. CPython 3.7)."
        ) from e
    return fxcorepy, ForexConnect, Common
```

- `FxcmClient.__init__` stores credential fields only — **no import**. So constructing any of the
  four surface objects succeeds with `forexconnect` absent (US3 AC-1, FR-004).
- First live operation (`connect()` → `get_history` / `send_request` / `get_table`) triggers
  `_load_forexconnect()`; absence raises `OperationalException` with the message above, never a
  bare `ModuleNotFoundError` (US3 AC-2/3, FR-006). `raise ... from e` keeps the cause chained but
  the primary message is actionable.

---

## 4. Symbol formatting placement (FR-009)

FXCM/ForexConnect symbols are already slash-format (`"EUR/USD"`), identical to the framework
canonical symbol (`ForexPair.get_symbol()`). So there is effectively **no transform** — the
adapter uppercases/strips defensively via a module-level `_fxcm_instrument(symbol)` helper inside
`fxcm_client.py` (or the executor), and nothing lives in the domain model. `ForexPair` loses its
two OANDA helpers and gains nothing (research.md "confirmed non-issues").

---

## 5. pyproject / extras changes (FR-005)

- Remove `oanda = []` from `[tool.poetry.extras]`; add `fxcm = ["forexconnect"]`.
- Add optional dep under `[tool.poetry.dependencies]`:
  `forexconnect = {version = ">=1.6.0", optional = true}`.
- Do **not** add `forexconnect` to the `all` extra — it is uninstallable on this repo's
  interpreter (C1); folding it into `all` would break `pip install .[all]` on 3.14. `ponytail:`
  comment noting `all` deliberately omits fxcm.
- `pip install .` with no extras pulls nothing new (FR-005, NFR-001). The `fxcm` extra will only
  resolve on cp35–37 (documented expectation, not a bug — spec note 5, C1).

---

## 6. Exports wiring (FR-003)

`infrastructure/__init__.py` mirror — replace exactly:

```python
# was:  from .oanda import OandaClient, OandaOHLCVDataProvider, \
#           OandaOrderExecutor, OandaPortfolioProvider
from .fxcm import FxcmClient, FxcmOHLCVDataProvider, \
    FxcmOrderExecutor, FxcmPortfolioProvider
```

and the four `__all__` entries `Oanda*` → `Fxcm*`. Keep scoping identical: **not** re-exported
from top-level `investing_algorithm_framework/__init__.py`, **not** added to
`get_default_data_providers()` (spec note 4 / A3) — this is what keeps FR-004 true (no SDK import
at package startup).

---

## 7. Component structure (responsibilities / boundaries)

- **FxcmClient** — owns session lifecycle. `connect()` (lazy-imports SDK, logs in with
  username/password/host/connection), `get_candles()`, `create_order()`, `get_order()`,
  `cancel_order()`, `get_position()`, `get_account()`, `disconnect()`. Thin wrapper over
  ForexConnect; translates SDK tables/rows into plain dicts/lists so the providers stay
  SDK-shape-agnostic (mirrors how `OandaClient` returned dicts).
- **FxcmOHLCVDataProvider** — `market_name = "FXCM"`, `timeframe_map` (framework TF →
  `m1/H1/D1/…`), `_download_ohlcv()` builds a client from the credential, calls `get_candles`,
  maps Bid OHLC → framework schema, returns the same polars schema as OANDA
  (`Datetime, Open, High, Low, Close, Volume`), degrades to an empty typed frame on failure
  (FR-011, parity with OANDA provider). `_storage_file_suffix()` → `"fxcm"`.
- **FxcmOrderExecutor** — `supports_market("FXCM")`. `execute_order()` maps framework
  `MARKET→true-market`, `LIMIT/STOP→ENTRY(RATE)`, submits, sets `external_id` + status
  (FILLED/PENDING/FAILED), never raises (returns FAILED order — OrderExecutor contract, US1 AC-5).
  Submits TP/SL when present (L1 caveat). `cancel_order()`.
- **FxcmPortfolioProvider** — `supports_market("FXCM")`. `get_order()` reads ORDERS/TRADES table
  rows and maps state → `OrderStatus` (L2); `get_position()` nets TRADES rows for the symbol,
  returns `Position` or `None` when flat. Never raises on not-found (returns `None`, contract).

---

## 8. Data flow (representative write + read)

**Write — BUY MARKET EUR/USD (US1):** strategy → `FxcmOrderExecutor.execute_order(portfolio,
order, FxcmCredential)` → build `FxcmClient` from credential → `client.connect()` (lazy import +
`ForexConnect().login(user, pass, host, "Demo")`) → `create_order_request(TRUE_MARKET_OPEN,
OFFER_ID="EUR/USD", ACCOUNT_ID, BUY_SELL=BUY, AMOUNT)` → `send_request` → `resp.order_id` →
set `order.external_id`, `order.status=FILLED` → return order. SDK failure → status FAILED,
logged, no crash (NFR-003).

**Read — OHLCV for backtest-style window (live only):** provider `_download_ohlcv` → client
`get_candles(instrument, timeframe, from, to)` → `ForexConnect.get_history` → Bid OHLC rows →
polars frame (`Datetime, Open, High, Low, Close, Volume`, UTC). No live session → clear error /
empty frame, not a crash (FR-011). Note: this path only runs on a supported interpreter with the
SDK installed (A4); on 3.14 it is exercised only through mocks.

---

## 9. Scaling / seams

- **Session reuse seam.** Each provider currently builds a client + logs in per call (mirrors
  OANDA's per-call `requests.Session`). If login latency matters, cache one live `FxcmClient` per
  credential on the provider. `ponytail:` comment marks the per-call login and the upgrade path.
  Not built now — single-user broker adapter, YAGNI.
- **Table-listener seam (L2).** Point-in-time table reads suffice for `get_order`/`get_position`.
  If real-time order-fill push is ever needed, `Common.subscribe_table_updates` is the documented
  hook; named here, not built.

---

## 10. Test plan (FR-013, NFR-004, Article V)

`tests/infrastructure/test_fxcm.py` mirrors `test_oanda.py`: patch the SDK boundary so the suite
is green on Python 3.14 with `forexconnect` **absent**.

- Mock target: patch `_load_forexconnect` (or the `FxcmClient` used by each provider) to return
  MagicMocks — the SDK name `forexconnect` is never imported, so tests pass without it installed
  (NFR-001, US2). This is the cleanest mock point because it is the *only* place the SDK is
  touched.
- Cases (parity with test_oanda.py): client get-candles / create-order / cancel / get-position;
  data provider `_download_ohlcv` returns the polars schema; executor market buy/sell → FILLED,
  limit/stop → PENDING, TP/SL passed through, `supports_market("FXCM")` true / others false;
  portfolio provider `get_order` found/not-found, `get_position` long/net-zero/not-found.
- **US3 error-path test (NFR-004):** force `import forexconnect` to fail and assert
  `_load_forexconnect()` raises `OperationalException` whose message names the package, the
  `[fxcm]` extra, and the interpreter constraint — and is **not** a bare `ModuleNotFoundError`.
  This locks the actionable-error contract against silent regression.
- `tests/domain/test_forex_models.py`: remove the two `*_oanda_format` tests.
- Gate: `SC-002` grep — `grep -ri oanda` over package/`docs`/`examples`/`README.md`/`pyproject`
  returns zero (spec exemptions: `specs/001-*`, `graphify-out/`).

---

## 11. Constitution Check (v1.2.0)

| Article | Status | Note |
|---|---|---|
| I — Spec before code | PASS | spec.md fully clarified; this plan is the *how*. |
| II — Minimal but scalable | PASS | Adapter swap, no new abstraction; seams named (§9). |
| III — Behavior sacred | PASS | Below-broker code (forex math, calendar, non-FXCM providers) untouched; only OANDA-named helpers removed (FR-009). |
| IV — Evidence over opinion | PASS | Capabilities cite doc URLs (research.md); unconfirmed → documented limitations L1–L5, not guesses. |
| V — Test-first | PASS | test_fxcm.py mirrors mock pattern; explicit US3 error-path test (NFR-004). |
| VI — Security / operability | PASS | Secrets via env vars (FXCM_*), never in code; failures logged + non-crashing (NFR-003). |
| VII — In-session | PASS | No external LLM. |
| VIII — Simplicity / reversibility | PASS | Subclass over base-model surgery; optional extra keeps `pip install .` reversible. |
| IX — Navigate via graph | DEVIATION | Graph (`graphify-out/`) not queried; surface is 7 known files enumerated in the task, read directly. Justified: bounded, explicitly-listed file set; graph query would not narrow it further. |

No violations requiring Complexity Tracking.

---

## 12. Risks

- **R1 — TP/SL parity (L1).** Inline attach-on-fill semantics unconfirmed from docs. Mitigation:
  executor submits TP/SL and the exact mechanism is verified on a supported interpreter (A4);
  documented as a known limitation, not a blocker (FR-007 routing).
- **R2 — Order-status model differs (L2).** Table-driven, not REST GET. Mitigation: point-in-time
  table read in `get_order`; listener seam named if push is later needed.
- **R3 — Live path untestable on 3.14 (C1).** Real session code never runs in CI. Mitigation:
  full mock coverage of the SDK boundary + human demo-account verification (SC-004 / A4). Accept
  that CI proves wiring/error-handling, not live fills.
- **R4 — Bid vs mid prices (L3).** FXCM OHLCV is Bid-based; OANDA was mid. Mitigation: documented;
  does not affect below-broker math (NFR-002).
- **R5 — Residual OANDA strings.** Miss a reference and SC-002 fails. Mitigation: the grep gate is
  the acceptance check; run it before marking done.
