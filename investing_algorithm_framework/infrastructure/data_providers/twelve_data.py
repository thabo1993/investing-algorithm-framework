import logging
from datetime import datetime

import polars as pl
import pandas as pd
import requests

from investing_algorithm_framework.domain import (
    OperationalException,
)
from .ohlcv_base import OHLCVDataProviderBase

logger = logging.getLogger("investing_algorithm_framework")

TIMEFRAME_TO_TWELVEDATA = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "45m": "45min",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "1d": "1day",
    "1W": "1week",
    "1M": "1month",
}


class TwelveDataOHLCVDataProvider(OHLCVDataProviderBase):
    market_name = "TWELVEDATA"
    timeframe_map = TIMEFRAME_TO_TWELVEDATA
    data_provider_identifier = "twelve_data_ohlcv_data_provider"
    BASE_URL = "https://api.twelvedata.com"

    def _download_ohlcv(
        self,
        symbol: str,
        time_frame,
        start_date: datetime,
        end_date: datetime,
    ) -> pl.DataFrame:
        api_key = self._get_api_key()
        interval = self._get_provider_interval()

        normalized_symbol = symbol.upper().replace("/", "")
        params = {
            "symbol": normalized_symbol,
            "interval": interval,
            "apikey": api_key,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "JSON",
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/time_series",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Twelve Data for {symbol}: {e}")
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

        if "status" in data and data.get("status") == "error":
            logger.error(
                f"Twelve Data API error for {symbol}: "
                f"{data.get('message', 'unknown')}"
            )
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

        values = data.get("values", [])
        if not values:
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

        records = []
        for entry in values:
            dt = pd.to_datetime(entry["datetime"])
            if dt.tz is None:
                dt = dt.tz_localize("UTC")

            records.append({
                "Datetime": dt,
                "Open": float(entry["open"]),
                "High": float(entry["high"]),
                "Low": float(entry["low"]),
                "Close": float(entry["close"]),
                "Volume": float(entry.get("volume", 0)),
            })

        df = pd.DataFrame(records)
        df = df.sort_values("Datetime").reset_index(drop=True)
        polars_df = pl.from_pandas(
            df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
        )
        return polars_df

    def _storage_file_suffix(self) -> str:
        return "twelve_data"
