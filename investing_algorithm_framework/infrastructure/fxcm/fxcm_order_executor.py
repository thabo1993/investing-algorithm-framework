import logging

from investing_algorithm_framework.domain import (
    OrderExecutor,
    Order,
    OrderStatus,
    OrderSide,
    OrderType,
    OperationalException,
)
from .fxcm_client import FxcmClient

logger = logging.getLogger("investing_algorithm_framework")

FXCM_ORDER_TYPE_MAP = {
    "MARKET": "MARKET",
    "LIMIT": "LIMIT",
    "STOP": "STOP",
    "STOP_LIMIT": "STOP_LIMIT",
}


def _normalize_instrument(symbol: str) -> str:
    return symbol.strip().upper().replace("_", "/")


class FxcmOrderExecutor(OrderExecutor):
    def execute_order(self, portfolio, order, market_credential) -> Order:
        order_type = order.get_order_type()
        order_side = order.get_order_side()
        symbol = order.get_symbol()
        instrument = _normalize_instrument(symbol)

        fxcm_type = FXCM_ORDER_TYPE_MAP.get(order_type)
        if fxcm_type is None:
            raise OperationalException(
                f"Order type {order_type} not supported by FXCM"
            )

        side = "SELL" if OrderSide.SELL.equals(order_side) else "BUY"
        units = abs(int(order.get_amount()))

        order_body = {
            "symbol": instrument,
            "type": fxcm_type,
            "side": side,
            "units": units,
        }

        if OrderType.LIMIT.equals(order_type):
            order_body["price"] = order.get_price()
        elif OrderType.STOP.equals(order_type):
            order_body["stop_price"] = order.get_stop_price()
        elif OrderType.STOP_LIMIT.equals(order_type):
            order_body["price"] = order.get_price()
            order_body["stop_price"] = order.get_stop_price()

        tp_price = order.get_take_profit_price()
        sl_price = order.get_stop_loss_price()

        if tp_price is not None:
            order_body["take_profit"] = tp_price
        if sl_price is not None:
            order_body["stop_loss"] = sl_price

        try:
            client = self._get_client(market_credential)
            response = client.create_order(order_body)

            status = response.get("status")
            order.external_id = response.get("external_id")

            # Sidecar broker status -> IAF domain OrderStatus.
            # NOTE (deliberate deviation from the reference executor this
            # mirrors): that reference sets OrderStatus.FILLED / PENDING /
            # FAILED, none of which exist in this IAF checkout — OrderStatus
            # is CREATED/OPEN/CLOSED/CANCELED/
            # EXPIRED/REJECTED (domain/models/order/order_status.py). We map to
            # valid members, matching IAF's CCXT integration semantics
            # (filled -> CLOSED, working -> OPEN, reject -> REJECTED).
            if status == "FILLED":
                order.status = OrderStatus.CLOSED.value
                order.price = float(response.get("price", 0))
                order.filled = abs(float(response.get("filled", 0)))
            elif status == "PENDING":
                order.status = OrderStatus.OPEN.value
                order.price = order.get_price()
            else:
                order.status = OrderStatus.REJECTED.value

            return order
        except Exception as e:
            logger.exception(e)
            order.status = OrderStatus.REJECTED.value
            return order

    def cancel_order(self, portfolio, order, market_credential) -> Order:
        client = self._get_client(market_credential)

        try:
            response = client.cancel_order(order.external_id)
            if response.get("status") == "CANCELED":
                order.status = OrderStatus.CANCELED.value
            else:
                order.status = OrderStatus.REJECTED.value
            return order
        except Exception as e:
            logger.exception(e)
            raise OperationalException(
                f"Could not cancel order {order.external_id}: {e}"
            )

    def supports_market(self, market):
        return market is not None and market.upper() == "FXCM"

    def _get_client(self, market_credential) -> FxcmClient:
        # FXCM broker credentials live only in the sidecar (research D8); the
        # market_credential here is not used for broker auth. The sidecar
        # connection is read from env by FxcmClient.
        return FxcmClient()
