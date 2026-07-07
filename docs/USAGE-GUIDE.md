# Usage Guide — End-to-End Workflows

> Full worked examples for common use cases.

## Forex / FX Trading

For a complete guide to forex trading — pip calculations, swap costs, margin utilization, market calendar filtering, and Oanda live integration — see:

👉 [`docs/FOREX-USAGE.md`](FOREX-USAGE.md)

Or jump straight to the runnable example:

👉 [`examples/forex/forex_strategy.py`](../examples/forex/forex_strategy.py)

## Crypto Trading (CCXT)

The framework's primary use case. See the tutorial series:

👉 [`examples/tutorial/README.md`](../examples/tutorial/README.md)

## Strategy Showcase

Collection of runnable strategy templates (trend following, mean reversion, cross-sectional momentum, multi-factor, pairs trading):

👉 [`examples/strategies_showcase/README.md`](../examples/strategies_showcase/README.md)

## Backtest Storage Layer

Managing thousands of backtests with the Tier-1 SQLite index, Tier-2 store adapters, and Tier-3 OHLCV deduplication:

👉 [`examples/storage_layer_demo/README.md`](../examples/storage_layer_demo/README.md)

## Quick Reference

| Task | Command / API |
|------|---------------|
| Install framework | `pip install investing-algorithm-framework` |
| Install forex extras | `pip install investing-algorithm-framework[oanda]` |
| Init project | `investing-algorithm-framework init` |
| Run backtest | `app.run_backtest(...)` |
| Run vector sweep | `app.run_vector_backtests(...)` |
| Generate HTML report | `BacktestReport(backtests).save("report.html")` |
| Start MCP server | `investing-algorithm-framework mcp` |
| Index backtest storage | `iaf index ./my-backtests/` |
| Rank backtests | `iaf rank ./my-backtests/ --by sharpe_ratio -n 20` |
