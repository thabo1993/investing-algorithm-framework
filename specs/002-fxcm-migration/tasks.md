# Tasks: FXCM Migration (replace OANDA)

**Feature:** 002-fxcm-migration
**Input:** `spec.md`, `plan.md` (authoritative HOW), `research.md`
**Whole-feature gate:** full `pytest` suite green on Python 3.14 (Windows) with `forexconnect`
NOT installed, and `grep -ri oanda` over package/`docs/`/`examples/`/`README.md`/`pyproject.toml`
returns zero (SC-001, SC-002, NFR-001).

Numbering starts at T201 to avoid collision with feature 001. `[P]` = parallelizable.
Each phase leaves the repo green.

---

## Phase A — Foundation: credential + lazy client (gate: pytest green, forexconnect absent)
- [ ] T201 `domain/models/market/fxcm_credential.py`: `FxcmCredential(MarketCredential)` with `market="FXCM"`, `username`/`password`/`connection`(Demo default)/`host_url` args, `initialize()` loading `FXCM_USERNAME`/`FXCM_PASSWORD`/`FXCM_CONNECTION`/`FXCM_URL` env vars and raising `OperationalException` when username/password missing, plus read-only properties (per plan §2). **(US1, FR-010)**
- [ ] T202 `infrastructure/fxcm/fxcm_client.py`: `FxcmClient` (stores credential fields only in `__init__`, no SDK import) + module-level lazy `_load_forexconnect()` helper and `_fxcm_instrument()` symbol passthrough (plan §3/§4). **(US1, US2, FR-004)**
- [ ] T203 [P] `tests/infrastructure/test_fxcm.py`: `FxcmCredential` env-var loading + missing-credential `OperationalException` cases. **(US1, FR-010)**
- [ ] T204 `tests/infrastructure/test_fxcm.py`: US3 error-path — force `import forexconnect` to fail, assert `_load_forexconnect()` raises `OperationalException` naming the package, the `[fxcm]` extra, and the interpreter constraint, and is NOT a bare `ModuleNotFoundError`. **(US3, FR-006, NFR-004)**

## Phase B — Providers with mocked SDK (gate: pytest green, SDK mocked/absent)
- [ ] T205 `infrastructure/fxcm/fxcm_data_provider.py`: `FxcmOHLCVDataProvider(OHLCVDataProviderBase)`, `market_name="FXCM"`, timeframe map, `_download_ohlcv` maps Bid OHLC → `Datetime,Open,High,Low,Close,Volume` polars schema, degrades to empty typed frame on failure, `_storage_file_suffix()`→`"fxcm"` (plan §7). **(US1, FR-011)**
- [ ] T206 `infrastructure/fxcm/fxcm_order_executor.py`: `FxcmOrderExecutor(OrderExecutor)`, `supports_market("FXCM")`, `execute_order` maps MARKET→true-market / LIMIT+STOP→ENTRY, sets `external_id`+FILLED/PENDING, submits TP/SL when present, never raises (returns FAILED on error), `cancel_order` (plan §7, L1/L4). **(US1, FR-002, FR-007, FR-008)**
- [ ] T207 `infrastructure/fxcm/fxcm_portfolio_provider.py`: `FxcmPortfolioProvider(PortfolioProvider)`, `supports_market("FXCM")`, `get_order` maps ORDERS/TRADES rows→`OrderStatus`, `get_position` nets TRADES rows→`Position` or `None` when flat, never raises on not-found (plan §7, L2). **(US1, FR-002, FR-008)**
- [ ] T208 `infrastructure/fxcm/__init__.py`: export `FxcmClient`, `FxcmOHLCVDataProvider`, `FxcmOrderExecutor`, `FxcmPortfolioProvider` (mirror OANDA package init). **(FR-003)**
- [ ] T209 `tests/infrastructure/test_fxcm.py`: mocked-SDK parity with `test_oanda.py` — patch the SDK boundary (`_load_forexconnect`/client); client get-candles/create/cancel/position; data provider `_download_ohlcv` schema; executor market buy/sell→FILLED, limit/stop→PENDING, TP/SL passthrough, `supports_market` true/false; portfolio `get_order` found/not-found, `get_position` long/net-zero/flat. **(US1, US2, FR-013)**

## Phase C — Delete OANDA + swap exports (gate: pytest green, no `oanda` in package source)
- [ ] T210 Delete `infrastructure/oanda/` package (all 5 files: `__init__.py`, `oanda_client.py`, `oanda_data_provider.py`, `oanda_order_executor.py`, `oanda_portfolio_provider.py`). **(US4, FR-001)**
- [ ] T211 `infrastructure/__init__.py`: replace the two OANDA import lines (23–24) and four `__all__` entries (68–71) with the `Fxcm*` equivalents; keep scoping identical (not top-level re-exported, not in `get_default_data_providers()`). **(US4, FR-003)**
- [ ] T212 `domain/models/market/__init__.py`: export `FxcmCredential` alongside `MarketCredential` (both import line and `__all__`). **(FR-010)**
- [ ] T213 `domain/models/forex/forex_pair.py`: delete `to_oanda_format()` and `from_oanda_format()` (lines 31–36); leave base/quote/Yahoo/Polygon helpers untouched. **(US4, FR-009)**
- [ ] T214 Delete `tests/infrastructure/test_oanda.py`; remove `test_to_oanda_format`/`test_from_oanda_format` from `tests/domain/test_forex_models.py`. **(US4, FR-001)**

## Phase D — Packaging + docs + final gate (gate: whole-feature gate above)
- [ ] T215 `pyproject.toml`: remove `oanda = []` extra, add `fxcm = ["forexconnect"]`, add optional dep `forexconnect = {version=">=1.6.0", optional=true}`; do NOT add to `all` extra (`ponytail:` comment on why — C1). **(FR-005)**
- [ ] T216 [P] `docs/FOREX-USAGE.md`: OANDA→FXCM wiring (credential + 3 providers), and an explicit callout that FXCM is NOT a backtest data source (live ForexConnect session only; public archive dead). **(US4, FR-012, C2/L5)**
- [ ] T217 [P] `examples/forex/forex_strategy.py`: OANDA→FXCM wiring; still runnable in backtest mode with `forexconnect` absent (live wiring env-var gated). **(US4, FR-012, A5)**
- [ ] T218 [P] `README.md` and `docs/USAGE-GUIDE.md`: replace OANDA references with FXCM (USAGE-GUIDE.md is in SC-002 grep scope; plan §1 listed only FOREX-USAGE.md/README). **(US4, FR-012)**
- [ ] T219 Final gate: full `pytest` on Python 3.14 without `forexconnect` green, AND `grep -ri oanda` over package/`docs/`/`examples/`/`README.md`/`pyproject.toml` returns zero (exempt `specs/001-*`, `graphify-out/`). **(SC-001, SC-002, NFR-001)**
