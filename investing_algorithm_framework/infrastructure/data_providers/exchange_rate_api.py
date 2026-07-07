import logging
from datetime import datetime
from typing import Union

import requests

from investing_algorithm_framework.domain import (
    DataProvider,
    DataType,
    DataSource,
    OperationalException,
    ImproperlyConfigured,
)

logger = logging.getLogger("investing_algorithm_framework")


class ExchangeRateAPITickerDataProvider(DataProvider):
    data_type = DataType.TICKER
    data_provider_identifier = "exchange_rate_api_ticker_provider"
    BASE_URL = "https://v6.exchangerate-api.com/v6"

    def __init__(
        self,
        symbol: str = None,
        market: str = None,
        data_provider_identifier: str = None,
        config=None,
    ):
        if data_provider_identifier is None:
            data_provider_identifier = self.data_provider_identifier

        super().__init__(
            symbol=symbol,
            market=market,
            data_provider_identifier=data_provider_identifier,
            data_type=DataType.TICKER,
            config=config,
        )

    def has_data(
        self,
        data_source: DataSource,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> bool:
        if not DataType.TICKER.equals(data_source.data_type):
            return False

        if data_source.market is None:
            return False

        return data_source.market.upper() == "EXCHANGE_RATE_API"

    def prepare_backtest_data(
        self,
        backtest_start_date,
        backtest_end_date,
        fill_missing_data: bool = False,
        show_progress: bool = False,
    ) -> None:
        pass

    def get_backtest_data(
        self,
        backtest_index_date: datetime,
        backtest_start_date: datetime = None,
        backtest_end_date: datetime = None,
        data_source: DataSource = None,
    ):
        return None

    def get_data(
        self,
        date: datetime = None,
        start_date: datetime = None,
        end_date: datetime = None,
        save: bool = False,
    ) -> dict:
        if self.market is None:
            raise OperationalException(
                "Market is not set. Please set the market "
                "before calling get_data."
            )

        if self.symbol is None:
            raise OperationalException(
                "Symbol is not set. Please set the symbol "
                "before calling get_data."
            )

        credential = self.get_credential(self.market)

        if credential is None:
            raise ImproperlyConfigured(
                "ExchangeRate-API requires an API key. "
                "Configure it with: "
                "MarketCredential(market='EXCHANGE_RATE_API', api_key='...')"
            )

        api_key = credential.api_key
        base_currency = self.symbol.upper().split("/")[0]

        try:
            response = requests.get(
                f"{self.BASE_URL}/{api_key}/latest/{base_currency}",
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching ExchangeRate-API data: {e}"
            )
            return {}

        if data.get("result") != "success":
            logger.error(
                f"ExchangeRate-API error: {data.get('error-type', 'unknown')}"
            )
            return {}

        quote_currency = self.symbol.upper().split("/")[1]
        rate = data.get("conversion_rates", {}).get(quote_currency)

        if rate is None:
            logger.error(
                f"ExchangeRate-API: no rate for {quote_currency} "
                f"in response"
            )
            return {}

        return {
            "symbol": self.symbol,
            "market": self.market,
            "bid": float(rate),
            "ask": float(rate),
            "mid": float(rate),
            "last": float(rate),
            "price": float(rate),
            "timestamp": data.get("time_last_update_utc"),
        }

    def copy(self, data_source: DataSource) -> "ExchangeRateAPITickerDataProvider":
        return ExchangeRateAPITickerDataProvider(
            symbol=data_source.symbol,
            market=data_source.market,
            data_provider_identifier=data_source.data_provider_identifier,
            config=self.config,
        )

    def get_number_of_data_points(
        self, start_date: datetime, end_date: datetime
    ) -> int:
        return 1

    def get_missing_data_dates(
        self, start_date: datetime, end_date: datetime
    ) -> list:
        return []

    def get_data_source_file_path(self) -> Union[str, None]:
        return None
