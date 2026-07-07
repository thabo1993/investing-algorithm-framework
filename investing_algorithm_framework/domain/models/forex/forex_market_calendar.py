from datetime import datetime, timedelta, timezone
from typing import Optional

import polars as pl


class ForexMarketCalendar:

    MARKET_OPEN_SUNDAY = 21  # Sunday 21:00 UTC (5pm ET)
    MARKET_CLOSE_FRIDAY = 21  # Friday 21:00 UTC (5pm ET)

    @staticmethod
    def is_market_open(dt: datetime) -> bool:
        weekday = dt.weekday()
        hour = dt.hour

        if weekday == 5:
            return False

        if weekday == 6:
            return hour >= ForexMarketCalendar.MARKET_OPEN_SUNDAY

        if weekday == 4 and hour > ForexMarketCalendar.MARKET_CLOSE_FRIDAY:
            return False

        return True

    @staticmethod
    def filter_market_hours(df: pl.DataFrame) -> pl.DataFrame:
        if "Datetime" not in df.columns:
            return df

        return df.filter(
            df["Datetime"].map_elements(
                ForexMarketCalendar.is_market_open, return_dtype=pl.Boolean
            )
        )

    @staticmethod
    def next_market_open(dt: datetime) -> datetime:
        if ForexMarketCalendar.is_market_open(dt):
            return dt

        weekday = dt.weekday()

        if weekday == 5:
            days_ahead = 1
        elif weekday == 6:
            days_ahead = 0
        else:
            days_ahead = (5 - weekday)
            if days_ahead <= 0:
                days_ahead = 7 + days_ahead

        next_open = dt.replace(
            hour=ForexMarketCalendar.MARKET_OPEN_SUNDAY,
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(days=days_ahead)

        return next_open

    @staticmethod
    def previous_market_close(dt: datetime) -> Optional[datetime]:
        if ForexMarketCalendar.is_market_open(dt):
            return dt

        weekday = dt.weekday()

        if weekday == 5:
            days_back = 1
        elif weekday == 6:
            days_back = 2
        else:
            days_back = (weekday + 2) % 7

        prev_close = dt.replace(
            hour=ForexMarketCalendar.MARKET_CLOSE_FRIDAY,
            minute=0,
            second=0,
            microsecond=0,
        ) - timedelta(days=days_back)

        return prev_close
