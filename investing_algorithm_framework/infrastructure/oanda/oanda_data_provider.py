import logging
from datetime import datetime

import polars as pl
import pandas as pd

from investing_algorithm_framework.domain import (
    OperationalException,
)
from investing_algorithm_framework.infrastructure.data_providers.ohlcv_base import (
    OHLCVDataProviderBase,
)
from .oanda_client import OandaClient

logger = logging.getLogger("investing_algorithm_framework")

OANDA_GRANULARITY_MAP = {
    "1m": "M1",
    "2m": "M2",
    "3m": "M3",
    "4m": "M4",
    "5m": "M5",
    "10m": "M10",
    "15m": "M15",
    "30m": "M30",
    "1h": "H1",
    "2h": "H2",
    "3h": "H3",
    "4h": "H4",
    "6h": "H6",
    "8h": "H8",
    "12h": "H12",
    "1d": "D",
    "1W": "W",
    "1M": "M",
}


def _normalize_instrument(symbol: str) -> str:
    return symbol.upper().replace("/", "_")


class OandaOHLCVDataProvider(OHLCVDataProviderBase):
    market_name = "OANDA"
    timeframe_map = OANDA_GRANULARITY_MAP
    data_provider_identifier = "oanda_ohlcv_data_provider"

    def _get_client(self, credential) -> OandaClient:
        return OandaClient(
            api_key=credential.api_key,
            account_id=credential.get("account_id", ""),
            environment=credential.get("environment", "practice"),
        )

    def _download_ohlcv(
        self,
        symbol: str,
        time_frame,
        start_date: datetime,
        end_date: datetime,
    ) -> pl.DataFrame:
        credential = self._get_credential()
        client = self._get_client(credential)
        instrument = _normalize_instrument(symbol)

        granularity = self._get_provider_interval()

        try:
            candles = client.get_candles(
                instrument=instrument,
                granularity=granularity,
                from_time=start_date,
                to_time=end_date,
            )
        except Exception as e:
            logger.error(
                f"Error fetching Oanda candles for {symbol}: {e}"
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

        if not candles:
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
        for c in candles:
            dt = pd.to_datetime(c["time"])
            if dt.tz is None:
                dt = dt.tz_localize("UTC")
            else:
                dt = dt.tz_convert("UTC")

            mid = c.get("mid", {})
            volume = c.get("volume", 0)

            records.append({
                "Datetime": dt,
                "Open": float(mid.get("o", 0)),
                "High": float(mid.get("h", 0)),
                "Low": float(mid.get("l", 0)),
                "Close": float(mid.get("c", 0)),
                "Volume": float(volume),
            })

        df = pd.DataFrame(records)
        df = df.sort_values("Datetime").reset_index(drop=True)
        polars_df = pl.from_pandas(
            df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
        )
        return polars_df

    def _storage_file_suffix(self) -> str:
        return "oanda"
