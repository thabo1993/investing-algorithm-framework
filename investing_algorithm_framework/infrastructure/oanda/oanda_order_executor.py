import logging

from investing_algorithm_framework.domain import (
    OrderExecutor,
    Order,
    OrderStatus,
    OrderSide,
    OrderType,
    OperationalException,
)
from .oanda_client import OandaClient

logger = logging.getLogger("investing_algorithm_framework")

OANDA_ORDER_TYPE_MAP = {
    "MARKET": "MARKET",
    "LIMIT": "LIMIT",
    "STOP": "STOP",
    "STOP_LIMIT": "STOP",
}


def _normalize_instrument(symbol: str) -> str:
    return symbol.upper().replace("/", "_")


class OandaOrderExecutor(OrderExecutor):
    def execute_order(self, portfolio, order, market_credential) -> Order:
        market = portfolio.market
        order_type = order.get_order_type()
        order_side = order.get_order_side()
        symbol = order.get_symbol()
        instrument = _normalize_instrument(symbol)

        oanda_type = OANDA_ORDER_TYPE_MAP.get(order_type)
        if oanda_type is None:
            raise OperationalException(
                f"Order type {order_type} not supported by Oanda"
            )

        units = order.get_amount()
        if OrderSide.SELL.equals(order_side):
            units = -units

        order_body = {
            "order": {
                "type": oanda_type,
                "instrument": instrument,
                "units": str(int(units)),
            }
        }

        if OrderType.LIMIT.equals(order_type):
            order_body["order"]["price"] = str(order.get_price())
        elif OrderType.STOP.equals(order_type):
            order_body["order"]["price"] = str(order.get_stop_price())
        elif OrderType.STOP_LIMIT.equals(order_type):
            order_body["order"]["priceBound"] = str(order.get_price())
            order_body["order"]["price"] = str(order.get_stop_price())

        tp_price = order.get_take_profit_price()
        sl_price = order.get_stop_loss_price()

        if tp_price is not None:
            order_body["order"]["takeProfitOnFill"] = {
                "price": str(tp_price),
            }

        if sl_price is not None:
            order_body["order"]["stopLossOnFill"] = {
                "price": str(sl_price),
            }

        try:
            client = self._get_client(market_credential)
            response = client.create_order(order_body)
            order_create = response.get("orderCreateTransaction", {})
            order_fill = response.get("orderFillTransaction", {})
            order_cancel = response.get("orderCancelTransaction", {})

            if order_fill:
                order.external_id = order_fill.get("id")
                order.status = OrderStatus.FILLED.value
                order.price = float(order_fill.get("price", 0))
                order.filled = abs(float(order_fill.get("units", 0)))
            elif order_create:
                order.external_id = order_create.get("id")
                order.status = OrderStatus.PENDING.value
                order.price = order.get_price()
            elif order_cancel:
                order.status = OrderStatus.FAILED.value
            else:
                order.status = OrderStatus.FAILED.value

            return order
        except Exception as e:
            logger.exception(e)
            order.status = OrderStatus.FAILED.value
            return order

    def cancel_order(self, portfolio, order, market_credential) -> Order:
        client = self._get_client(market_credential)

        try:
            client.cancel_order(order.external_id)
            order.status = OrderStatus.CANCELED.value
            return order
        except Exception as e:
            logger.exception(e)
            raise OperationalException(
                f"Could not cancel order {order.external_id}: {e}"
            )

    def supports_market(self, market):
        return market is not None and market.upper() == "OANDA"

    def _get_client(self, market_credential) -> OandaClient:
        return OandaClient(
            api_key=market_credential.api_key,
            account_id=market_credential.get("account_id", ""),
            environment=market_credential.get("environment", "practice"),
        )
