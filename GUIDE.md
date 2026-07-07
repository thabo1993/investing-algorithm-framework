# Investing Algorithm Framework — Guide: Mass Strategy Testing & Ranking

This guide covers what the framework is, how it fits together, and — since
your goal is testing hundreds/thousands of strategy variants in parallel and
surfacing the ones with Sharpe > 1.65 — a concrete pattern for that workflow
end to end.

## 1. What it is

A Python framework covering the full quant workflow with one `TradingStrategy`
class reused at every stage:

```
define strategy → vector-backtest (fast, thousands of variants)
                → rank/filter with the storage layer (SQLite index, ms-fast)
                → event-backtest the survivors (realistic execution)
                → compare in one HTML dashboard
                → deploy the winner (local / AWS Lambda / Azure Functions)
```

Core objects:

| Object | Role |
|---|---|
| `TradingStrategy` | You subclass it — `symbols`, `data_sources`, `generate_buy_signals`/`generate_sell_signals` (or vectorized equivalents), plus risk rules |
| `PositionSize`, `StopLossRule`, `TakeProfitRule`, `ScalingRule`, `CooldownRule`, `TradingCost` | Declarative risk/execution rules, enforced identically by both engines |
| `Backtest` / `BacktestMetrics` | Result of one strategy run — holds `sharpe_ratio`, `sortino_ratio`, `max_drawdown`, `calmar_ratio`, etc. |
| `.iafbt` bundle | Compressed, versioned container for a backtest result (zstd + msgpack) — ~21x smaller than a raw directory dump |
| Tier-1 SQLite index | One row per bundle, every scalar metric as a column — filters/ranks 10k+ backtests in sub-100ms without decoding any bundle |
| `BacktestReport` | Self-contained HTML dashboard — no server needed |

## 2. Install

```bash
pip install investing-algorithm-framework
investing-algorithm-framework init          # scaffold a project
```

## 3. Define a strategy

```python
from typing import Dict, Any
import pandas as pd
from pyindicators import ema, rsi, crossover, crossunder

from investing_algorithm_framework import (
    TradingStrategy, DataSource, TimeUnit, DataType,
    PositionSize, StopLossRule, TakeProfitRule,
)


class RSIEMACrossoverStrategy(TradingStrategy):
    time_unit = TimeUnit.HOUR
    interval = 2
    symbols = ["BTC", "ETH"]
    data_sources = [
        DataSource(
            identifier="BTC_ohlcv", symbol="BTC/EUR",
            data_type=DataType.OHLCV, time_frame="2h",
            market="BITVAVO", pandas=True, warmup_window=100,
        ),
    ]

    position_sizes = [PositionSize(symbol="BTC", percentage_of_portfolio=20)]
    stop_losses = [StopLossRule(symbol="BTC", percentage_threshold=5, trailing=True)]
    take_profits = [TakeProfitRule(symbol="BTC", percentage_threshold=10, sell_percentage=50)]

    # Params you'll sweep over — expose them as constructor args so
    # each variant is a distinct instance, not a distinct class.
    def __init__(self, ema_short=12, ema_long=26, rsi_period=14, rsi_oversold=30):
        super().__init__()
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold

    def generate_buy_signals(self, data: Dict[str, Any]) -> Dict[str, pd.Series]:
        signals = {}
        for symbol in self.symbols:
            df = data[f"{symbol}_ohlcv"]
            ema_s = ema(df, period=self.ema_short, source_column="Close", result_column="ema_s")
            ema_l = ema(ema_s, period=self.ema_long, source_column="Close", result_column="ema_l")
            cross = crossover(ema_l, first_column="ema_s", second_column="ema_l", result_column="x")
            r = rsi(df, period=self.rsi_period, source_column="Close", result_column="rsi")
            oversold = r["rsi"] < self.rsi_oversold
            recent_cross = cross["x"].rolling(window=10).max() > 0
            signals[symbol] = (oversold & recent_cross).fillna(False)
        return signals

    def generate_sell_signals(self, data: Dict[str, Any]) -> Dict[str, pd.Series]:
        signals = {}
        for symbol in self.symbols:
            df = data[f"{symbol}_ohlcv"]
            ema_s = ema(df, period=self.ema_short, source_column="Close", result_column="ema_s")
            ema_l = ema(ema_s, period=self.ema_long, source_column="Close", result_column="ema_l")
            cross = crossunder(ema_l, first_column="ema_s", second_column="ema_l", result_column="x")
            r = rsi(df, period=self.rsi_period, source_column="Close", result_column="rsi")
            overbought = r["rsi"] >= 70
            recent_cross = cross["x"].rolling(window=10).max() > 0
            signals[symbol] = (overbought & recent_cross).fillna(False)
        return signals
```

More templates (trend following, mean reversion, pairs trading, market
making, options...) live in `examples/strategies_showcase/`.

## 4. Generate hundreds/thousands of variants

Sweep the parameter grid, instantiate one strategy object per combination.
This is plain Python — no framework magic needed here:

```python
import itertools

param_grid = {
    "ema_short": [8, 12, 16, 20],
    "ema_long": [26, 34, 50],
    "rsi_period": [10, 14, 21],
    "rsi_oversold": [20, 25, 30, 35],
}

keys = list(param_grid)
combos = list(itertools.product(*param_grid.values()))
strategies = [
    RSIEMACrossoverStrategy(**dict(zip(keys, combo)))
    for combo in combos
]
print(f"{len(strategies)} variants")   # 4*3*3*4 = 144, scale the grid up as needed
```

## 5. Run them all — vector backtest, parallel

`App.run_vector_backtests` is built for exactly this: it takes a `List[TradingStrategy]`,
runs them in parallel worker processes, checkpoints progress so a crash on
variant #8,000 doesn't lose #1–7,999, and writes each result out as an
`.iafbt` bundle.

```python
from investing_algorithm_framework import create_app, BacktestDateRange

app = create_app()
# register your data sources / market credentials as usual, then:

date_range = BacktestDateRange(start="2022-01-01", end="2024-01-01")

backtests = app.run_vector_backtests(
    strategies=strategies,
    backtest_date_range=date_range,
    n_workers=None,              # None = use all CPU cores
    batch_size=50,                # variants processed per worker batch
    use_checkpoints=True,         # resume-safe for large sweeps
    checkpoint_batch_size=25,
    backtest_storage_directory="./backtests",   # each result saved as .iafbt
    show_progress=True,
    continue_on_error=True,       # one bad variant doesn't kill the run
)
```

For thousands of variants, run this on a machine with enough cores — it's
CPU-bound, embarrassingly parallel across strategies. `continue_on_error=True`
plus checkpoints means you can `Ctrl+C` and resume later.

## 6. Rank and filter for Sharpe > 1.65

Two ways depending on whether the in-memory `List[Backtest]` still fits, or
you're querying a large saved directory.

### 6a. In-memory, right after the run

```python
from investing_algorithm_framework.analysis.ranking import rank_results
from investing_algorithm_framework import BacktestEvaluationFocus

winners = rank_results(
    backtests,
    focus=BacktestEvaluationFocus.RISK_ADJUSTED,   # weights favor Sharpe/Sortino/Calmar
    filter_fn={
        "sharpe_ratio": lambda v: v is not None and v > 1.65,
    },
)
print(f"{len(winners)} strategies clear Sharpe > 1.65")
top = winners[:20]
```

### 6b. From disk, at scale — the Tier-1 SQLite index

This is the piece built specifically for "compare thousands of backtests
without opening every bundle." Once `run_vector_backtests` has written a
directory of `.iafbt` files:

```bash
# Build the SQLite index once (or with --incremental after new runs land)
iaf index ./backtests/

# Sharpe > 1.65, sorted, top 20 — sub-100ms even over 10k+ bundles
iaf rank ./backtests/ \
    --by sharpe_ratio \
    --where "summary_sharpe_ratio > 1.65" \
    -n 20
```

Or from Python:

```python
from investing_algorithm_framework.cli.index_command import (
    build_index, rank_index,
)

build_index("./backtests")

top = rank_index(
    "./backtests",
    by="sharpe_ratio",
    where="summary_sharpe_ratio > 1.65",
    limit=20,
)
for row in top:
    print(row["algorithm_id"], row["summary_sharpe_ratio"])
```

Or raw SQL if you want a custom report (win rate + trade count constraints, etc.):

```bash
sqlite3 ./backtests/index.sqlite "
  SELECT algorithm_id, summary_sharpe_ratio, summary_max_drawdown,
         summary_number_of_trades
    FROM backtest_index
   WHERE summary_sharpe_ratio > 1.65
     AND summary_number_of_trades > 30
   ORDER BY summary_sharpe_ratio DESC
   LIMIT 20;
"
```

## 7. Validate the survivors with a realistic event-driven backtest

Vector backtests are for fast signal screening — validate anything that
clears your Sharpe bar with the slower, order-by-order event engine before
trusting it:

```python
winning_strategies = [strategies[i] for i in winner_indices]  # map back from step 6

event_backtests = app.run_backtests(
    strategies=winning_strategies,
    backtest_date_range=date_range,
    n_workers=None,
)

final = rank_results(
    event_backtests,
    filter_fn={"sharpe_ratio": lambda v: v is not None and v > 1.65},
)
```

## 8. Compare in one dashboard

```python
from investing_algorithm_framework import BacktestReport

report = BacktestReport.open(backtests=final[:10])   # top 10 side by side
report.save("top_strategies.html")                    # self-contained, open in browser
```

## 9. Deploy the actual winner

Same `TradingStrategy` class, no rewrite:

```python
app.add_strategy(final[0].strategy)   # or reconstruct from the winning params
app.run(mode="live")                  # local
# or: investing-algorithm-framework init --type aws_lambda / azure_function
```

## Practical notes for a "thousands of strategies" app

- **Grid size**: `itertools.product` grows fast — 4 params x 5 values each is
  625 variants. Start smaller, widen once you know which axes matter.
- **`n_workers`**: leave as `None` to use all cores; set it explicitly if
  you're sharing the machine with other jobs.
- **`use_checkpoints=True`** is not optional at this scale — a sweep of
  10k variants that dies at 90% without checkpoints is a wasted afternoon.
- **Two-stage funnel**: vector-backtest everything (cheap), only
  event-backtest the Sharpe > 1.65 survivors (expensive, realistic). Don't
  event-backtest the full grid.
- **The SQLite index is the reason this scales** — it's what lets you filter
  10k+ results by Sharpe in milliseconds instead of decoding 10k Parquet
  blobs. See `examples/storage_layer_demo/README.md` for the full CLI
  cheatsheet (`iaf index` / `iaf list` / `iaf rank` / `iaf migrate-store`).
- **Overfitting check**: a Sharpe > 1.65 out of a 625-variant grid search is
  exactly the situation permutation testing exists for — run
  `BacktestPermutationTest` on your top candidates before trusting the number
  (`examples/tutorial/notebooks/06_robustness_analysis.ipynb`).

## Where to go next

- `examples/tutorial/notebooks/03_param_sweep.ipynb` — runnable param-sweep walkthrough
- `examples/storage_layer_demo/demo.py` — end-to-end storage layer + dashboard demo
- `examples/strategies_showcase/` — 26 strategy templates across styles
- Docs: https://coding-kitties.github.io/investing-algorithm-framework/
