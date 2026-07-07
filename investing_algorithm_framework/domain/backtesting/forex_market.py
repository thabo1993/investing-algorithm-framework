import logging

import polars as pl

from investing_algorithm_framework.domain.models.forex import (
    ForexMarketCalendar,
)
from investing_algorithm_framework.domain.constants import (
    FOREX_MARKET_IDENTIFIER,
)

logger = logging.getLogger("investing_algorithm_framework")


def apply_market_calendar_filter(
    df: pl.DataFrame,
    market: str,
    datetime_column: str = "Datetime",
) -> pl.DataFrame:
    if market != FOREX_MARKET_IDENTIFIER:
        return df

    if datetime_column not in df.columns:
        return df

    before = len(df)
    filtered = df.filter(
        df[datetime_column].map_elements(
            ForexMarketCalendar.is_market_open,
            return_dtype=pl.Boolean,
        )
    )
    after = len(filtered)
    removed = before - after

    if before > 0 and (removed / before) > 0.10:
        logger.warning(
            f"Market calendar filter removed {removed}/{before} "
            f"({removed / before:.1%}) rows — data quality signal"
        )

    return filtered
