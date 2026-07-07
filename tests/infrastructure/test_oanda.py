import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone

import polars as pl


class TestOandaClient(unittest.TestCase):
    @patch("investing_algorithm_framework.infrastructure.oanda.oanda_client"
           ".requests.Session")
    def setUp(self, mock_session):
        self.mock_session_instance = MagicMock()
        mock_session.return_value = self.mock_session_instance

        from investing_algorithm_framework.infrastructure.oanda \
            import OandaClient

        self.client = OandaClient(
            api_key="test_key",
            account_id="test_account",
            environment="practice",
        )

    def test_get_account_summary(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "account": {"id": "test_account", "balance": "10000.0"}
        }
        result = self.client.get_account_summary()
        self.assertEqual(result["id"], "test_account")
        self.mock_session_instance.get.assert_called_once()

    def test_get_pricing(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "prices": [{
                "instrument": "EUR_USD",
                "bids": [{"price": "1.1050"}],
                "asks": [{"price": "1.1052"}],
            }]
        }
        result = self.client.get_pricing(["EUR_USD"])
        self.assertEqual(len(result), 1)

    def test_get_candles(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "candles": [{
                "time": "2024-01-01T00:00:00Z",
                "mid": {"o": "1.10", "h": "1.11", "l": "1.09", "c": "1.105"},
                "volume": 1000,
            }]
        }
        result = self.client.get_candles("EUR_USD", granularity="D")
        self.assertEqual(len(result), 1)

    def test_create_order(self):
        self.mock_session_instance.post.return_value.json.return_value = {
            "orderCreateTransaction": {"id": "123", "units": "10000"},
            "orderFillTransaction": {
                "id": "124", "price": "1.1050", "units": "10000"
            },
        }
        result = self.client.create_order({"order": {"type": "MARKET"}})
        self.assertIn("orderCreateTransaction", result)
        self.mock_session_instance.post.assert_called_once()

    def test_cancel_order(self):
        self.mock_session_instance.put.return_value.json.return_value = {}
        result = self.client.cancel_order("123")
        self.mock_session_instance.put.assert_called_once()

    def test_get_open_orders(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "orders": [{"id": "1", "state": "PENDING"}]
        }
        result = self.client.get_open_orders()
        self.assertEqual(len(result), 1)

    def test_get_position_found(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "position": {
                "instrument": "EUR_USD",
                "long": {"units": "10000"},
                "short": {"units": "0"},
            }
        }
        result = self.client.get_position("EUR_USD")
        self.assertIsNotNone(result)
        self.assertEqual(result["instrument"], "EUR_USD")

    def test_get_position_not_found(self):
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_error = HTTPError(response=mock_response)
        self.mock_session_instance.get.side_effect = mock_error

        result = self.client.get_position("USD_SOS")
        self.assertIsNone(result)

    def test_get_open_positions(self):
        self.mock_session_instance.get.return_value.json.return_value = {
            "positions": [{"instrument": "EUR_USD"}]
        }
        result = self.client.get_open_positions()
        self.assertEqual(len(result), 1)


class TestOandaOHLCVDataProvider(unittest.TestCase):
    @patch(
        "investing_algorithm_framework.infrastructure.oanda"
        ".oanda_data_provider.OandaClient"
    )
    def setUp(self, mock_client_class):
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client

        from investing_algorithm_framework.infrastructure.oanda \
            import OandaOHLCVDataProvider

        self.provider = OandaOHLCVDataProvider()
        self.provider._credential = MagicMock()

    def test_download_ohlcv(self):
        self.mock_client.get_candles.return_value = [
            {
                "time": "2024-01-01T00:00:00.000000000Z",
                "mid": {"o": "1.10", "h": "1.11", "l": "1.09", "c": "1.105"},
                "volume": 1000,
            },
        ]

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 3, tzinfo=timezone.utc)

        result = self.provider._download_ohlcv(
            "EUR/USD", None, start, end
        )
        self.assertEqual(len(result), 1)

    def test_storage_file_suffix(self):
        self.assertEqual(
            self.provider._storage_file_suffix(), "oanda"
        )


class TestOandaOrderExecutor(unittest.TestCase):
    @patch(
        "investing_algorithm_framework.infrastructure.oanda"
        ".oanda_order_executor.OandaClient"
    )
    def setUp(self, mock_client_class):
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client

        from investing_algorithm_framework.infrastructure.oanda \
            import OandaOrderExecutor

        self.executor = OandaOrderExecutor()
        self.mock_credential = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio.market = "OANDA"

    def test_supports_market(self):
        self.assertTrue(self.executor.supports_market("OANDA"))
        self.assertFalse(self.executor.supports_market("BINANCE"))

    def test_execute_market_buy_order(self):
        self.mock_client.create_order.return_value = {
            "orderCreateTransaction": {"id": "txn_1", "units": "10000"},
            "orderFillTransaction": {
                "id": "fill_1", "price": "1.1050", "units": "10000"
            },
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            amount=10000,
        )
        result = self.executor.execute_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.FILLED.value)

    def test_execute_market_sell_order(self):
        self.mock_client.create_order.return_value = {
            "orderCreateTransaction": {"id": "txn_2", "units": "-10000"},
            "orderFillTransaction": {
                "id": "fill_2", "price": "1.1050", "units": "-10000"
            },
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.SELL.value,
            order_type=OrderType.MARKET.value,
            amount=10000,
        )
        result = self.executor.execute_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.FILLED.value)

    def test_execute_limit_order(self):
        self.mock_client.create_order.return_value = {
            "orderCreateTransaction": {"id": "txn_3", "units": "10000"},
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.LIMIT.value,
            amount=10000,
            price=1.1000,
        )
        result = self.executor.execute_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.PENDING.value)

    def test_execute_stop_order(self):
        self.mock_client.create_order.return_value = {
            "orderCreateTransaction": {"id": "txn_4", "units": "10000"},
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.STOP.value,
            amount=10000,
            stop_price=1.1050,
        )
        result = self.executor.execute_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.PENDING.value)

    def test_execute_order_with_tp_sl(self):
        self.mock_client.create_order.return_value = {
            "orderCreateTransaction": {"id": "txn_5", "units": "10000"},
            "orderFillTransaction": {
                "id": "fill_5", "price": "1.1050", "units": "10000"
            },
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            amount=10000,
            take_profit_price=1.1100,
            stop_loss_price=1.0950,
        )

        result = self.executor.execute_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.FILLED.value)

        call_kwargs = self.mock_client.create_order.call_args[1]["body"]
        tp_of = call_kwargs["order"].get("takeProfitOnFill")
        sl_of = call_kwargs["order"].get("stopLossOnFill")
        self.assertIsNotNone(tp_of)
        self.assertIsNotNone(sl_of)
        self.assertEqual(tp_of["price"], "1.1100")
        self.assertEqual(sl_of["price"], "1.0950")

    def test_cancel_order(self):
        self.mock_client.cancel_order.return_value = {}

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            amount=10000,
            external_id="order_1",
        )
        result = self.executor.cancel_order(
            self.portfolio, order, self.mock_credential
        )
        self.assertEqual(result.status, OrderStatus.CANCELED.value)
        self.mock_client.cancel_order.assert_called_once_with("order_1")


class TestOandaPortfolioProvider(unittest.TestCase):
    @patch(
        "investing_algorithm_framework.infrastructure.oanda"
        ".oanda_portfolio_provider.OandaClient"
    )
    def setUp(self, mock_client_class):
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client

        from investing_algorithm_framework.infrastructure.oanda \
            import OandaPortfolioProvider

        self.provider = OandaPortfolioProvider()
        self.mock_credential = MagicMock()
        self.portfolio = MagicMock()
        self.portfolio.market = "OANDA"
        self.portfolio.id = 1

    def test_supports_market(self):
        self.assertTrue(self.provider.supports_market("OANDA"))
        self.assertFalse(self.provider.supports_market("BINANCE"))

    def test_get_order_found(self):
        self.mock_client.get_order.return_value = {
            "order": {
                "id": "order_1",
                "instrument": "EUR_USD",
                "units": "10000",
                "state": "FILLED",
                "type": "MARKET",
                "price": "1.1050",
            }
        }

        from investing_algorithm_framework.domain.models.order import (
            Order, OrderSide, OrderType, OrderStatus,
        )

        internal_order = Order(
            target_symbol="EUR",
            trading_symbol="USD",
            order_side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            amount=10000,
        )
        internal_order.id = 42

        result = self.provider.get_order(
            self.portfolio, internal_order, self.mock_credential
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 42)
        self.assertEqual(result.external_id, "order_1")
        self.assertEqual(result.status, OrderStatus.FILLED.value)

    def test_get_order_not_found(self):
        self.mock_client.get_order.side_effect = Exception("Not found")

        internal_order = MagicMock()
        internal_order.external_id = "nonexistent"

        result = self.provider.get_order(
            self.portfolio, internal_order, self.mock_credential
        )
        self.assertIsNone(result)

    def test_get_position_long(self):
        self.mock_client.get_position.return_value = {
            "instrument": "EUR_USD",
            "long": {"units": "10000"},
            "short": {"units": "0"},
        }

        result = self.provider.get_position(
            self.portfolio, "EUR/USD", self.mock_credential
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, "EUR/USD")
        self.assertEqual(result.amount, 10000)

    def test_get_position_net_zero(self):
        self.mock_client.get_position.return_value = {
            "instrument": "EUR_USD",
            "long": {"units": "0"},
            "short": {"units": "0"},
        }
        result = self.provider.get_position(
            self.portfolio, "EUR/USD", self.mock_credential
        )
        self.assertIsNone(result)

    def test_get_position_not_found(self):
        self.mock_client.get_position.side_effect = Exception("Not found")
        result = self.provider.get_position(
            self.portfolio, "USD/SOS", self.mock_credential
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
