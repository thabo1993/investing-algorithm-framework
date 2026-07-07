# Feature Specification: FXCM Migration (replace OANDA)

**Feature Branch:** `002-fxcm-migration`
**Created:** 2026-07-05
**Status:** Draft
**Input:** Replace the OANDA live-forex integration with FXCM (via Gehtsoft's ForexConnect SDK)
as a lazy-optional adapter. Full structural replacement of the OANDA surface; the test suite
must stay green on Python 3.14 with `forexconnect` NOT installed.

> Defines **what** and **why** — never *how*. No tech stack, no APIs, no code here — that
> belongs in `plan.md`. Mark every genuine open question **[NEEDS CLARIFICATION: …]**.

---

## Executive Summary

The framework (feature 001) added live forex trading via OANDA's v20 REST API through a four-part
infrastructure surface: `OandaClient`, `OandaOHLCVDataProvider`, `OandaOrderExecutor`,
`OandaPortfolioProvider`, exported from `investing_algorithm_framework.infrastructure`.

This feature **replaces that surface with FXCM**, accessed through Gehtsoft's ForexConnect SDK
(PyPI `forexconnect`). The OANDA modules are removed; FXCM provides the same four-part surface
(client, OHLCV data provider, order executor, portfolio provider) so that forex strategies keep
working with a one-line broker swap.

The defining constraint is that **`forexconnect` cannot be installed in the project's own
Python 3.14 environment** (see Constraints C1). It is therefore a **lazy-optional adapter**: the
SDK is imported only when a live FXCM session is actually opened, it is offered as an optional
pip extra, and its absence produces a clear, actionable error rather than an import crash. This
keeps `pip install .` and the full test suite green on Python 3.14 with `forexconnect` absent.

Everything *below* the broker boundary — the forex domain models (`ForexPair`, `LotSize`,
`PipCalculator`, `SwapRate`, `MarginRequirement`), pip/swap/margin backtesting, the 24/5 calendar,
and the free data providers (Yahoo, Alpha Vantage, Polygon, FRED, Twelve Data, ExchangeRate-API) —
is provider-agnostic and stays exactly as it is. This is a migration, not a green-field feature.

---

## User Scenarios & Testing

### User Story 1 — Forex strategy author connects FXCM instead of OANDA (Priority: P1)

As a forex strategy author, I want to wire my strategy to a FXCM account instead of OANDA, so I
can execute live forex trades through my broker using the same framework surface I already know.

**Why priority:** This is the whole point of the migration. OANDA is being retired; FXCM must
take its place as the live-trading broker without forcing users to rewrite their strategy code.

**Independent test:** With `forexconnect` installed on a supported interpreter and valid FXCM
demo credentials, a user registers the FXCM data provider, order executor, and portfolio provider
on the app, starts in LIVE mode, and a market order placed through the framework reaches FXCM and
comes back with an external id and a FILLED/PENDING status.

**Acceptance scenarios:**

1. **Given** a FXCM credential registered on the app and `forexconnect` installed, **When** the
   framework starts in LIVE mode, **Then** the FXCM order executor and portfolio provider
   initialize by opening a ForexConnect session and report the account's available balance.
2. **Given** a live FXCM session, **When** a `BUY MARKET` order for EUR/USD is submitted, **Then**
   the order is placed through FXCM, an `external_id` is returned, and the order status is
   reported (FILLED for a market order, PENDING for a resting order).
3. **Given** a live FXCM session, **When** the portfolio provider is asked for the EUR/USD
   position, **Then** the current net position (or `None` when flat) is returned from FXCM's
   account state.
4. **Given** an order carrying take-profit and/or stop-loss prices, **When** it is executed on
   FXCM, **Then** the attached TP/SL are submitted with the order (parity with the OANDA
   `takeProfitOnFill` / `stopLossOnFill` behaviour that this replaces).
5. **Given** the FXCM session cannot be opened or a request fails, **When** an order is submitted,
   **Then** the executor does not crash the framework; it reports the order as FAILED and logs the
   cause (parity with the OANDA executor's existing failure handling).

### User Story 2 — Developer installs and tests IAF on Python 3.14 without forexconnect (Priority: P1)

As a framework developer or contributor on Python 3.14 (Windows), I want to install the framework
and run the full test suite **without** `forexconnect` present, so that the SDK's inability to
install on my interpreter never blocks development, CI, or release.

**Why priority:** `forexconnect` has no wheel for Python 3.14 and no sdist (Constraint C1). If it
were a hard dependency, `pip install .` and every test run on the project's own interpreter would
fail. This story is what makes the migration installable at all.

**Independent test:** On Python 3.14 with `forexconnect` NOT installed, `pip install .` completes
cleanly and the full `pytest` suite passes, including the FXCM adapter tests (which mock the SDK
boundary).

**Acceptance scenarios:**

1. **Given** a clean Python 3.14 Windows environment, **When** `pip install .` is run, **Then** it
   completes successfully and does **not** attempt to install `forexconnect`.
2. **Given** `forexconnect` is not installed, **When** the full `pytest` suite runs, **Then** every
   test passes, and the FXCM adapter tests exercise the adapter with the SDK boundary mocked
   (mirroring the existing `tests/infrastructure/test_oanda.py` pattern).
3. **Given** `forexconnect` is not installed, **When** any part of the package is imported
   (including `from investing_algorithm_framework.infrastructure import <FXCM surface>`), **Then**
   the import succeeds — the SDK is never imported at module-load time.

### User Story 3 — User without the SDK gets a clear, actionable error (Priority: P1)

As a user who wants live FXCM trading but has not installed the SDK (or is on an interpreter where
it cannot be installed), I want a clear, actionable error the moment I try to open a live session,
so I understand exactly what to install and why it is separate.

**Why priority:** A silent failure or a raw `ModuleNotFoundError` on `forexconnect` would strand
users with no guidance. The lazy-optional design is only correct if the failure mode is
self-explanatory.

**Independent test:** With `forexconnect` absent, constructing the FXCM adapter succeeds, but the
first call that needs a live session raises an error whose message names the missing package, the
install extra, and the interpreter constraint.

**Acceptance scenarios:**

1. **Given** `forexconnect` is not installed, **When** a user constructs a FXCM data provider,
   order executor, or portfolio provider, **Then** construction succeeds without error (no SDK
   needed to build the object).
2. **Given** `forexconnect` is not installed, **When** a user triggers an operation that requires a
   live FXCM session (fetch data, place order, sync portfolio), **Then** the framework raises a
   clear, actionable error — an `OperationalException` (or equivalent) whose message states that
   `forexconnect` is required, how to install it (the optional extra), and that it is unavailable
   on unsupported interpreters such as Python 3.14.
3. **Given** the error is raised, **When** the user reads it, **Then** it does not leak an
   unhandled `ImportError`/`ModuleNotFoundError` stack as the primary message.

### User Story 4 — No OANDA reference remains in package, docs, or examples (Priority: P2)

As a maintainer, I want every OANDA reference removed from the shipped package, documentation, and
examples, so that no user is misled into wiring a broker the framework no longer supports.

**Why priority:** A half-migrated codebase that still mentions OANDA in docs, exports, or the
forex domain model is worse than either broker alone — it invites bug reports and broken tutorials.

**Independent test:** A case-insensitive search for `oanda` across the package source, `docs/`,
`examples/`, `README.md`, and `pyproject.toml` returns no matches (with the exemptions in AC-3).

**Acceptance scenarios:**

1. **Given** the migration is complete, **When** `grep -ri oanda` is run over
   `investing_algorithm_framework/`, `docs/`, `examples/`, `README.md`, and `pyproject.toml`,
   **Then** it returns nothing.
2. **Given** the forex domain model (`ForexPair`), **When** it is inspected, **Then** it contains
   no OANDA-named members — the `to_oanda_format()` / `from_oanda_format()` methods are removed
   (see FR-009, resolved).
3. **Given** the search in AC-1, **When** it runs, **Then** the historical SDD records under
   `specs/001-forex-support/` and any `graphify-out/` graph artifacts are **exempt** (they are
   history, not shipped surface).
4. **Given** the forex example and the forex usage guide, **When** a user follows them, **Then**
   they demonstrate FXCM wiring end to end with no OANDA references.

---

## Requirements

### Functional Requirements

- **FR-001:** The system MUST remove the OANDA integration entirely: the
  `investing_algorithm_framework/infrastructure/oanda/` package and its four modules
  (`OandaClient`, `OandaOHLCVDataProvider`, `OandaOrderExecutor`, `OandaPortfolioProvider`), their
  exports from `infrastructure/__init__.py`, and their tests.
- **FR-002:** The system MUST provide a FXCM integration exposing the same four-part surface —
  a client, an OHLCV data provider, an order executor, and a portfolio provider — each an
  implementation of the same base classes the OANDA versions implemented (`OHLCVDataProviderBase`,
  `OrderExecutor`, `PortfolioProvider`). No new parallel abstraction hierarchy is introduced.
- **FR-003:** The FXCM surface MUST be exported from `investing_algorithm_framework.infrastructure`
  so that existing import sites migrate by name only (same import location as the OANDA surface).
- **FR-004:** `forexconnect` MUST NOT be a hard/import-time dependency. Importing the package, or
  the FXCM surface, MUST succeed with `forexconnect` absent. The SDK MUST be imported lazily, only
  when a live FXCM session is opened.
- **FR-005:** `forexconnect` MUST be offered as an **optional** pip extra (replacing the `oanda`
  extra). `pip install .` with no extras MUST NOT pull in `forexconnect`.
- **FR-006:** When an operation requires a live FXCM session and `forexconnect` is not importable,
  the system MUST raise a clear, actionable error (per US3) — never a bare `ModuleNotFoundError`
  as the surfaced error.
- **FR-007:** The FXCM order executor MUST support the order types the OANDA executor supported —
  Market, Limit, Stop, Stop-Limit — and MUST carry attached Take-Profit and Stop-Loss instructions
  through to FXCM. The portfolio provider MUST map FXCM order/position state back to the
  framework's `Order`/`Position`/`OrderStatus` model. *[Resolved 2026-07-05: capability parity is a
  research question, not a user decision — Plan phase resolves it in `research.md`; whatever
  ForexConnect cannot natively express becomes a documented limitation, not a blocker.]*
- **FR-008:** The FXCM order executor and portfolio provider MUST report the market identifier
  `FXCM` (i.e. `supports_market("FXCM")` is true), replacing the OANDA identifier.
- **FR-009:** The forex domain model MUST be provider-neutral: `ForexPair.to_oanda_format()` and
  `ForexPair.from_oanda_format()` MUST be **removed outright** (FR AC in US4-2). *[Resolved
  2026-07-05: their only in-package callers are the OANDA modules being deleted; any FXCM-specific
  symbol formatting lives inside the FXCM adapter, not the domain model.]*
- **FR-010:** FXCM credential inputs MUST be accepted through **dedicated FXCM credential fields**
  — the credential model is extended with explicit `username` / `password` / `connection`
  (Demo/Real, default Demo) / `host_url` fields rather than overloading `api_key` / `secret_key`.
  Environment variables: `FXCM_USERNAME`, `FXCM_PASSWORD`, `FXCM_CONNECTION`, `FXCM_URL`,
  replacing the `OANDA_API_KEY` / `OANDA_ACCOUNT_ID` / `OANDA_ENVIRONMENT` set. *[Resolved
  2026-07-05: user decision — dedicated fields over MarketCredential reuse; Plan phase designs the
  extension (subclass vs. new fields) so existing credential-loading paths keep working.]*
- **FR-011:** The FXCM OHLCV data provider MUST source historical candles through the live
  ForexConnect session (the only available FXCM path — see Constraint C2). It MUST return the same
  polars OHLCV schema the OANDA provider returned (`Datetime, Open, High, Low, Close, Volume`) and
  MUST degrade gracefully (clear error, no crash) when the session is unavailable.
- **FR-012:** All documentation and examples MUST be migrated to FXCM: `docs/FOREX-USAGE.md`,
  `examples/forex/forex_strategy.py`, the forex mentions in `README.md`, and the `oanda` extra in
  `pyproject.toml`. No OANDA reference may remain in shipped surface (US4).
- **FR-013:** The FXCM adapter MUST ship with unit tests that mock the ForexConnect SDK boundary,
  following the pattern of `tests/infrastructure/test_oanda.py`, so the tests pass with the SDK
  absent (US2).

### Key Entities (affected)

- **FXCM adapter surface** — the four replacement components (client, OHLCV data provider, order
  executor, portfolio provider). Behavioural parity with the OANDA surface at the framework
  boundary; the broker-specific transport (REST vs ForexConnect session) is a plan-level concern.
- **ForexPair** — existing provider-agnostic domain model. Only its OANDA-named helper methods
  change (FR-009); base/quote parsing, pip/display decimals, and the Yahoo/Polygon format helpers
  are untouched.
- **MarketCredential** — existing credential model. The forex broker credential shape changes from
  OANDA's (api_key + account_id + environment) to FXCM's (see FR-010).

### Non-Functional Requirements

- **NFR-001:** `pip install .` and the full `pytest` suite MUST be green on Python 3.14 (Windows)
  with `forexconnect` NOT installed. This is a hard acceptance gate.
- **NFR-002:** No behaviour change below the broker boundary. The forex domain models, pip/swap/
  margin math, 24/5 calendar, and non-FXCM data providers produce identical outputs before and
  after this migration (Constitution Article III).
- **NFR-003:** FXCM session/connection failures (auth failure, network loss, SDK absent) MUST NOT
  crash the framework — parity with the OANDA integration's existing failure handling.
- **NFR-004:** The lazy-import error path (US3) MUST be covered by a test that runs with the SDK
  absent, so the actionable-error contract cannot silently regress.

---

## Success Criteria

- **SC-001:** On Python 3.14 (Windows) with `forexconnect` absent, `pip install .` completes
  cleanly and `pytest` reports the full suite passing.
- **SC-002:** `grep -ri oanda` over the package source, `docs/`, `examples/`, `README.md`, and
  `pyproject.toml` returns zero matches (excluding `specs/001-forex-support/` and `graphify-out/`).
- **SC-003:** `from investing_algorithm_framework.infrastructure import <the four FXCM components>`
  succeeds with `forexconnect` absent; the first operation requiring a live session raises an
  error naming the package, the install extra, and the interpreter constraint.
- **SC-004:** With `forexconnect` installed on a supported interpreter and valid FXCM demo
  credentials, a market order placed through the framework is accepted by FXCM and returns an
  external id and a resolved status (parity with the OANDA acceptance from feature 001).
- **SC-005:** A user following `docs/FOREX-USAGE.md` and `examples/forex/forex_strategy.py` wires a
  FXCM strategy end to end with no OANDA references and no import errors when the SDK is absent
  (backtest mode still runs without the SDK).

---

## Out of Scope

- **Other live brokers:** Interactive Brokers, IG, Saxo, re-adding OANDA — out of scope. FXCM is
  the sole live forex broker this feature delivers.
- **Backtest data from a public FXCM archive:** FXCM's free public candle archive is dead
  (Constraint C2). This feature does **not** promise backtest OHLCV from any FXCM public source;
  backtesting continues to use the existing free data providers.
- **Making `forexconnect` installable on Python 3.14:** out of the framework's control (no wheel,
  no sdist, proprietary, pinned to old numpy/pandas). Not attempted.
- **Changes to forex domain math, backtesting, or non-FXCM data providers** beyond the OANDA-name
  neutralization in FR-009. Behaviour is preserved.
- **Rollover/swap, pip, margin feature changes** — delivered by feature 001 and unchanged here.

---

## Constraints

- **C1 — `forexconnect` cannot install on the project interpreter (verified 2026-07-05):** Latest
  PyPI releases are 1.6.43 (2021) / 1.6.5 (2022). Wheels exist only for cp35/36/37 (Windows+Linux)
  plus a single cp310 macOS-ARM wheel; there is **no sdist**. It pins numpy 1.14 / pandas 0.23 and
  is proprietary-licensed. It therefore **cannot** be installed in the project's Python 3.14
  Windows venv. This is the direct reason the adapter is lazy-optional and the tests mock the SDK.
- **C2 — No FXCM public backtest archive (verified 2026-07-05):** FXCM's free public candle archive
  (`candledata.fxcorporate.com`, per github.com/fxcm/MarketData) is dead — the documented URLs
  return 404. Historical FXCM OHLCV is available only through the live ForexConnect session, or not
  at all. The spec MUST NOT promise backtest data from a FXCM public archive (see Out of Scope).
- **C3 — Import safety:** Because C1 makes the SDK absent in the project environment, the FXCM
  modules must be importable and constructible with `forexconnect` absent; the SDK import happens
  only at session-open time (FR-004).

---

## Assumptions

- **A1:** The `MarketCredential` + env-var mechanism (feature 001) is the right home for FXCM
  credentials; only the field/env-var names change (subject to FR-010 clarification).
- **A2:** ForexConnect's session model can satisfy the four-part surface's needs (auth, history,
  order placement/cancellation, position/account retrieval) closely enough that no new base
  abstraction is required — the same base classes the OANDA surface implemented suffice.
- **A3:** The OANDA surface is the *only* place OANDA leaks into shipped code besides the two
  `ForexPair` helper methods; verified by `grep -ri oanda` (7 in-package files: the 5 OANDA module
  files, the `infrastructure/__init__.py` exports, and `forex_pair.py`).
- **A4:** Live FXCM verification (SC-004) is performed on a supported interpreter (e.g. a cp37
  environment) or a FXCM demo account by a human; it is not part of the automated Python 3.14 CI
  gate, which runs with the SDK mocked.
- **A5:** The forex example must still run in backtest mode with `forexconnect` absent (it does
  today for OANDA — live wiring is gated behind an env-var check); this behaviour is preserved.

---

## Notes for planning (surprises found in the OANDA surface)

These are observations that change scope; they are recorded here so `plan.md` accounts for them.

1. **`ForexPair` carries OANDA-named methods.** `to_oanda_format()` (returns `EUR_USD`) and
   `from_oanda_format()` live in the provider-neutral domain model
   (`domain/models/forex/forex_pair.py:31-36`). The "no oanda anywhere" gate (US4) forces these to
   change even though they are not part of the infrastructure surface. Their only in-package
   callers are the OANDA modules being deleted, so removal is low-risk; naming of any replacement
   is the open question (FR-009).
2. **Credential shape mismatch.** OANDA used `api_key` + `account_id` + `environment`. ForexConnect
   authenticates with **user id + password + connection type (Demo/Real) + host URL** — a different
   shape than `MarketCredential`'s `api_key`/`secret_key`. This is the most consequential open
   design point (FR-010) and drives docs, env-var names, and the example rewrite.
3. **Data provider needs a live session.** The OANDA OHLCV provider fetched candles over REST with
   from/to; FXCM history comes only through an authenticated ForexConnect session (Constraint C2).
   So the FXCM data provider — unlike a keyless public provider — cannot function without the SDK
   and credentials, and cannot run in the Python 3.14 test environment at all. Tests must mock it,
   and users must be told FXCM is not a backtest data source.
4. **Export locations.** The OANDA surface is exported from `infrastructure/__init__.py` (lines
   23-24 and 68-71) but is **not** re-exported from the top-level package `__init__.py`. The FXCM
   surface should match that placement. OANDA is also **not** in `get_default_data_providers()`, so
   there is no auto-registration path that would import the SDK at startup — good for FR-004.
5. **Extra name.** `pyproject.toml` has an `oanda` extra (currently empty of a real dependency);
   this becomes a `fxcm` extra that declares `forexconnect`. Because of C1 the extra will only
   resolve on supported interpreters — this is expected and must be documented, not "fixed".

---

## Open Questions — all resolved 2026-07-05 (Clarify phase)

- **NC-1 (FR-010):** ✔ Dedicated FXCM credential fields (`username`/`password`/`connection`/
  `host_url`; env vars `FXCM_USERNAME`/`FXCM_PASSWORD`/`FXCM_CONNECTION`/`FXCM_URL`) — user
  decision; extension mechanism designed in Plan.
- **NC-2 (FR-007):** ✔ Routed to Plan-phase `research.md`; unsupported capabilities become
  documented limitations.
- **NC-3 (FR-009):** ✔ Remove the OANDA-named `ForexPair` helpers outright; FXCM formatting lives
  in the adapter.

The migration decisions themselves (replace OANDA with FXCM, lazy-optional adapter, same four-part
surface, tests green with `forexconnect` absent) are **final** and not open.
