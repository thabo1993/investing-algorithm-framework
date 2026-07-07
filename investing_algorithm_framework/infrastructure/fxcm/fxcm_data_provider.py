import logging
from datetime import datetime

import polars as pl
import pandas as pd

from investing_algorithm_framework.infrastructure.data_providers.ohlcv_base \
    import OHLCVDataProviderBase
from .fxcm_client import FxcmClient

logger = logging.getLogger("investing_algorithm_framework")

# Framework TimeFrame string -> ForexConnect timeframe token. Mirrors the
# shape of the reference broker's granularity map.
# ponytail: exact ForexConnect tokens confirmed against the installed SDK in
# live mode (T007 / research open-question 2); simulated feed accepts these.
FXCM_TIMEFRAME_MAP = {
    "1m": "m1",
    "5m": "m5",
    "15m": "m15",
    "30m": "m30",
    "1h": "H1",
    "2h": "H2",
    "3h": "H3",
    "4h": "H4",
    "6h": "H6",
    "8h": "H8",
    "1d": "D1",
    "1W": "W1",
    "1M": "M1",
}

_EMPTY_SCHEMA = {
    "Datetime": pl.Datetime("us", "UTC"),
    "Open": pl.Float64,
    "High": pl.Float64,
    "Low": pl.Float64,
    "Close": pl.Float64,
    "Volume": pl.Float64,
}


def _normalize_instrument(symbol: str) -> str:
    # FXCM wire format is BASE/QUOTE with a slash (e.g. "EUR/USD"), not the
    # underscore BASE_QUOTE form. Indices (DXY) pass through unchanged.
    return symbol.strip().upper().replace("_", "/")


class FxcmOHLCVDataProvider(OHLCVDataProviderBase):
    market_name = "FXCM"
    timeframe_map = FXCM_TIMEFRAME_MAP
    data_provider_identifier = "fxcm_ohlcv_data_provider"

    def _get_client(self) -> FxcmClient:
        # No MarketCredential here: the sidecar is the sole holder of FXCM
        # credentials (research D8). The modern process only needs the
        # loopback sidecar connection, which FxcmClient reads from env.
        return FxcmClient()

    def _download_ohlcv(
        self,
        symbol: str,
        time_frame,
        start_date: datetime,
        end_date: datetime,
    ) -> pl.DataFrame:
        client = self._get_client()
        instrument = _normalize_instrument(symbol)
        timeframe = self._get_provider_interval()

        try:
            candles = client.get_candles(
                symbol=instrument,
                timeframe=timeframe,
                from_time=start_date,
                to_time=end_date,
            )
        except Exception as e:
            logger.error(
                f"Error fetching FXCM candles for {symbol}: {e}"
            )
            return pl.DataFrame(schema=_EMPTY_SCHEMA)

        if not candles:
            return pl.DataFrame(schema=_EMPTY_SCHEMA)

        records = []
        for c in candles:
            dt = pd.to_datetime(c["time"])
            if dt.tz is None:
                dt = dt.tz_localize("UTC")
            else:
                dt = dt.tz_convert("UTC")

            records.append({
                "Datetime": dt,
                "Open": float(c.get("o", 0)),
                "High": float(c.get("h", 0)),
                "Low": float(c.get("l", 0)),
                "Close": float(c.get("c", 0)),
                "Volume": float(c.get("volume", 0)),
            })

        df = pd.DataFrame(records)
        df = df.sort_values("Datetime").reset_index(drop=True)
        polars_df = pl.from_pandas(
            df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
        )
        return polars_df

    def _storage_file_suffix(self) -> str:
        return "fxcm"
