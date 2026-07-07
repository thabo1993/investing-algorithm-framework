import logging
from typing import Union

from investing_algorithm_framework.domain import (
    PortfolioProvider,
    Order,
    OrderStatus,
    OrderSide,
    OrderType,
    Position,
    OperationalException,
)
from .oanda_client import OandaClient

logger = logging.getLogger("investing_algorithm_framework")


def _normalize_instrument(symbol: str) -> str:
    return symbol.upper().replace("/", "_")


def _denormalize_instrument(instrument: str) -> str:
    return instrument.replace("_", "/")


OANDA_ORDER_STATE_MAP = {
    "PENDING": "PENDING",
    "FILLED": "FILLED",
    "TRIGGERED": "PENDING",
    "CANCELLED": "CANCELED",
    "REJECTED": "FAILED",
    "EXPIRED": "EXPIRED",
}


class OandaPortfolioProvider(PortfolioProvider):
    def get_order(
        self, portfolio, order, market_credential
    ) -> Union[Order, None]:
        client = self._get_client(market_credential)

        try:
            data = client.get_order(order.external_id)
        except Exception:
            return None

        order_data = data.get("order")
        if order_data is None:
            return None

        return self._order_from_oanda(order_data, order.id)

    def get_position(
        self, portfolio, symbol, market_credential
    ) -> Union[Position, None]:
        client = self._get_client(market_credential)
        instrument = _normalize_instrument(symbol)

        try:
            position_data = client.get_position(instrument)
        except Exception as e:
            logger.error(f"Error fetching Oanda position for {symbol}: {e}")
            return None

        if position_data is None:
            return None

        long = position_data.get("long", {})
        short = position_data.get("short", {})

        long_units = float(long.get("units", 0))
        short_units = float(short.get("units", 0))

        net_units = long_units + short_units

        if net_units == 0:
            return None

        return Position(
            symbol=symbol,
            amount=abs(net_units),
            portfolio_id=portfolio.id,
        )

    def supports_market(self, market) -> bool:
        return market is not None and market.upper() == "OANDA"

    def _get_client(self, market_credential) -> OandaClient:
        return OandaClient(
            api_key=market_credential.api_key,
            account_id=market_credential.get("account_id", ""),
            environment=market_credential.get("environment", "practice"),
        )

    @staticmethod
    def _order_from_oanda(
        oanda_data: dict, internal_id=None
    ) -> Order:
        instrument = oanda_data.get("instrument", "")
        symbol = _denormalize_instrument(instrument)
        target_symbol = symbol.split("/")[0]
        trading_symbol = symbol.split("/")[1]

        units = float(oanda_data.get("units", 0))
        order_side = OrderSide.BUY.value if units > 0 else OrderSide.SELL.value
        amount = abs(units)

        oanda_state = oanda_data.get("state", "PENDING")
        status = OANDA_ORDER_STATE_MAP.get(oanda_state, "PENDING")

        order_type = "MARKET"
        oanda_type = oanda_data.get("type", "MARKET")
        if oanda_type == "LIMIT":
            order_type = "LIMIT"
        elif oanda_type == "STOP":
            order_type = "STOP"

        order = Order(
            id=internal_id,
            external_id=oanda_data.get("id"),
            target_symbol=target_symbol,
            trading_symbol=trading_symbol,
            price=float(oanda_data.get("price", 0)),
            amount=amount,
            status=status,
            order_type=order_type,
            order_side=order_side,
            filled=amount if status == "FILLED" else 0,
            remaining=0 if status == "FILLED" else amount,
        )
        return order
