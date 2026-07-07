import logging
from typing import Union

from investing_algorithm_framework.domain import (
    PortfolioProvider,
    Order,
    Position,
)
from .fxcm_client import FxcmClient

logger = logging.getLogger("investing_algorithm_framework")


def _normalize_instrument(symbol: str) -> str:
    return symbol.strip().upper().replace("_", "/")


class FxcmPortfolioProvider(PortfolioProvider):
    def get_order(
        self, portfolio, order, market_credential
    ) -> Union[Order, None]:
        # ponytail: the frozen sidecar IPC contract exposes no single-order
        # GET (contracts/fxcm-sidecar-ipc.md) — live order/trade state arrives
        # via the WS position/account stream and the POST /orders response.
        # Return None (base contract: "return None if not found, never
        # throw"). Add GET /orders/{id} to the contract only if per-order
        # polling is ever required.
        return None

    def get_position(
        self, portfolio, symbol, market_credential
    ) -> Union[Position, None]:
        client = self._get_client(market_credential)
        instrument = _normalize_instrument(symbol)

        try:
            positions = client.get_positions()
        except Exception as e:
            logger.error(f"Error fetching FXCM position for {symbol}: {e}")
            return None

        for pos in positions:
            if _normalize_instrument(str(pos.get("symbol", ""))) == instrument:
                net_units = float(pos.get("net_units", 0))
                if net_units == 0:
                    return None
                return Position(
                    symbol=symbol,
                    amount=abs(net_units),
                    portfolio_id=portfolio.id,
                )

        return None

    def supports_market(self, market) -> bool:
        return market is not None and market.upper() == "FXCM"

    def _get_client(self, market_credential) -> FxcmClient:
        # FXCM credentials live only in the sidecar (research D8); connection
        # info is read from env by FxcmClient.
        return FxcmClient()
