import logging
from datetime import datetime

import polars as pl
import pandas as pd

from investing_algorithm_framework.domain import (
    DataSource,
    OperationalException,
)
from .ohlcv_base import OHLCVDataProviderBase

logger = logging.getLogger("investing_algorithm_framework")

FRED_SERIES_MAP = {
    "EUR/USD": "DEXUSEU",
    "GBP/USD": "DEXUSUK",
    "USD/JPY": "DEXJPUS",
    "USD/CHF": "DEXSZUS",
    "USD/CAD": "DEXCAUS",
    "AUD/USD": "DEXUSAL",
    "NZD/USD": "DEXUSNZ",
    "USD/SEK": "DEXSDUS",
    "USD/NOK": "DEXNOUS",
    "USD/DKK": "DEXDKUS",
    "INR/USD": "DEXINUS",
    "CNY/USD": "DEXCHUS",
    "MXN/USD": "DEXMXUS",
    "ZAR/USD": "DEXSFUS",
    "SGD/USD": "DEXSIUS",
    "HKD/USD": "DEXHKUS",
    "TWD/USD": "DEXTAUS",
    "KRW/USD": "DEXKOUS",
    "BRL/USD": "DEXBZUS",
    "THB/USD": "DEXTHUS",
}


def _ensure_fredapi():
    try:
        import fredapi
        return fredapi
    except ImportError:
        raise ImportError(
            "fredapi is required for FRED data provider. "
            "Install it with: pip install fredapi"
        )


class FREDOHLCVDataProvider(OHLCVDataProviderBase):
    market_name = "FRED"
    timeframe_map = {"1d": "1d", "1W": "1w", "1M": "1m"}
    data_provider_identifier = "fred_ohlcv_data_provider"

    def _get_fred_series_id(self, symbol: str) -> str:
        normalized = symbol.upper().replace("-", "/")
        series_id = FRED_SERIES_MAP.get(normalized)

        if series_id is None:
            raise OperationalException(
                f"FRED does not support symbol '{symbol}'. "
                f"Supported pairs: {list(FRED_SERIES_MAP.keys())}"
            )
        return series_id

    def _download_ohlcv(
        self,
        symbol: str,
        time_frame,
        start_date: datetime,
        end_date: datetime,
    ) -> pl.DataFrame:
        _ensure_fredapi()
        from fredapi import Fred

        api_key = self._get_api_key()
        fred = Fred(api_key=api_key)
        series_id = self._get_fred_series_id(symbol)

        try:
            series = fred.get_series(
                series_id,
                observation_start=start_date.strftime("%Y-%m-%d"),
                observation_end=end_date.strftime("%Y-%m-%d"),
            )
        except Exception as e:
            logger.error(f"Error fetching FRED data for {series_id}: {e}")
            return pl.DataFrame(
                schema={
                    "Datetime": pl.Datetime("us", "UTC"),
                    "Open": pl.Float64,
                    "High": pl.Float64,
                    "Low": pl.Float64,
                    "Close": pl.Float64,
                    "Volume": pl.Float64,
                }
            )

        if series is None or len(series) == 0:
            return pl.DataFrame(
                schema={
                    "Datetime": pl.Datetime("us", "UTC"),
                    "Open": pl.Float64,
                    "High": pl.Float64,
                    "Low": pl.Float64,
                    "Close": pl.Float64,
                    "Volume": pl.Float64,
                }
            )

        df = series.reset_index()
        df.columns = ["Datetime", "Close"]

        # FRED provides end-of-day rates only
        df["Open"] = df["Close"]
        df["High"] = df["Close"]
        df["Low"] = df["Close"]
        df["Volume"] = 0

        # Ensure UTC timezone
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        if df["Datetime"].dt.tz is None:
            df["Datetime"] = df["Datetime"].dt.tz_localize("UTC")

        df = df.sort_values("Datetime").reset_index(drop=True)

        polars_df = pl.from_pandas(
            df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
        )
        return polars_df

    def _validate_symbol(self, data_source: DataSource) -> bool:
        try:
            self._get_fred_series_id(data_source.symbol)
            return True
        except OperationalException:
            return False

    def _storage_file_suffix(self) -> str:
        return "fred"
