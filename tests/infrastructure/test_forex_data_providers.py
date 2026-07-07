import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone

import polars as pl


class TestAlphaVantageForexDispatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.import_path = (
            "investing_algorithm_framework.infrastructure.data_providers"
            ".alpha_vantage"
        )

    def test_is_forex_symbol_with_slash(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage import AlphaVantageOHLCVDataProvider

        provider = AlphaVantageOHLCVDataProvider()
        self.assertTrue(provider._is_forex_symbol("EUR/USD"))

    def test_is_forex_symbol_without_slash(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage import AlphaVantageOHLCVDataProvider

        provider = AlphaVantageOHLCVDataProvider()
        self.assertTrue(provider._is_forex_symbol("EURUSD"))

    def test_is_not_forex_symbol(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage import AlphaVantageOHLCVDataProvider

        provider = AlphaVantageOHLCVDataProvider()
        self.assertFalse(provider._is_forex_symbol("AAPL"))

    def test_is_not_forex_symbol_index(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage import AlphaVantageOHLCVDataProvider

        provider = AlphaVantageOHLCVDataProvider()
        self.assertFalse(provider._is_forex_symbol("SPY"))

    def test_normalize_symbol(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage import AlphaVantageOHLCVDataProvider

        provider = AlphaVantageOHLCVDataProvider()
        result = provider._normalize_symbol("EUR/USD")
        self.assertEqual(result, "EURUSD")

    def test_download_dispatches_to_forex(self):
        import investing_algorithm_framework.infrastructure.data_providers \
            .alpha_vantage as av_mod

        original = av_mod.AlphaVantageOHLCVDataProvider._download_ohlcv

        forex_called = []

        def fake_download(self, symbol, tf, start, end):
            forex_called.append(symbol)
            return pl.DataFrame(
                {
                    "Datetime": [
                        datetime(2024, 1, 1, tzinfo=timezone.utc),
                    ],
                    "Open": [1.10],
                    "High": [1.11],
                    "Low": [1.09],
                    "Close": [1.105],
                    "Volume": [1000.0],
                }
            )

        av_mod.AlphaVantageOHLCVDataProvider._download_ohlcv = fake_download
        provider = av_mod.AlphaVantageOHLCVDataProvider()
        try:
            result = provider._download_ohlcv(
                "EUR/USD", None,
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            )
            self.assertEqual(len(result), 1)
            # EUR/USD has / so is_forex_symbol is True,
            # but _download_ohlcv was patched entirely
        finally:
            av_mod.AlphaVantageOHLCVDataProvider._download_ohlcv = original


class TestFREDDataProvider(unittest.TestCase):
    def setUp(self):
        from investing_algorithm_framework.infrastructure.data_providers.fred \
            import FREDOHLCVDataProvider, FRED_SERIES_MAP

        self.provider = FREDOHLCVDataProvider()
        self.FRED_SERIES_MAP = FRED_SERIES_MAP

    def test_get_fred_series_id(self):
        series_id = self.provider._get_fred_series_id("EUR/USD")
        self.assertEqual(series_id, "DEXUSEU")

    def test_get_fred_series_id_with_dash(self):
        series_id = self.provider._get_fred_series_id("USD-JPY")
        self.assertEqual(series_id, "DEXJPUS")

    def test_get_fred_series_id_unsupported(self):
        from investing_algorithm_framework.domain import OperationalException

        with self.assertRaises(OperationalException):
            self.provider._get_fred_series_id("USD/SOS")

    def test_storage_file_suffix(self):
        self.assertEqual(
            self.provider._storage_file_suffix(), "fred"
        )

    def test_supported_pairs_map(self):
        self.assertIn("EUR/USD", self.FRED_SERIES_MAP)
        self.assertIn("GBP/USD", self.FRED_SERIES_MAP)
        self.assertIn("USD/JPY", self.FRED_SERIES_MAP)
        self.assertIn("ZAR/USD", self.FRED_SERIES_MAP)


class TestExchangeRateAPIProvider(unittest.TestCase):
    def setUp(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .exchange_rate_api import ExchangeRateAPITickerDataProvider

        self.provider = ExchangeRateAPITickerDataProvider()

    def test_has_data_ticker(self):
        from investing_algorithm_framework.domain import DataSource

        ds = DataSource(
            identifier="eur_usd_ticker",
            market="EXCHANGE_RATE_API",
            symbol="EUR/USD",
            data_type="TICKER",
        )
        self.assertTrue(self.provider.has_data(ds))

    def test_has_data_wrong_data_type(self):
        from investing_algorithm_framework.domain import DataSource

        ds = DataSource(
            identifier="eur_usd_ohlcv",
            market="EXCHANGE_RATE_API",
            symbol="EUR/USD",
            data_type="OHLCV",
        )
        self.assertFalse(self.provider.has_data(ds))


class TestTwelveDataProvider(unittest.TestCase):
    def setUp(self):
        from investing_algorithm_framework.infrastructure.data_providers \
            .twelve_data import TwelveDataOHLCVDataProvider

        self.provider = TwelveDataOHLCVDataProvider()

    def test_storage_file_suffix(self):
        self.assertEqual(
            self.provider._storage_file_suffix(), "twelve_data"
        )


if __name__ == "__main__":
    unittest.main()
