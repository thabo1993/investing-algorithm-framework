import logging
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("investing_algorithm_framework")

OANDA_LIVE = "https://api-fxtrade.oanda.com"
OANDA_PRACTICE = "https://api-fxpractice.oanda.com"
OANDA_DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept-Datetime-Format": "RFC3339",
}


class OandaClient:
    def __init__(
        self,
        api_key: str,
        account_id: str,
        environment: str = "practice",
    ):
        self.api_key = api_key
        self.account_id = account_id

        if environment == "live":
            self.base_url = OANDA_LIVE
        else:
            self.base_url = OANDA_PRACTICE

        self._session = requests.Session()
        self._session.headers.update(OANDA_DEFAULT_HEADERS)
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/v3/accounts/{self.account_id}{path}"

    def _get(self, path: str, params: dict = None) -> dict:
        response = self._session.get(self._url(path), params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, body: dict = None) -> dict:
        response = self._session.post(
            self._url(path), json=body, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _put(self, path: str, body: dict = None) -> dict:
        response = self._session.put(
            self._url(path), json=body, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_account_summary(self) -> dict:
        data = self._get("")
        return data.get("account", {})

    def get_pricing(self, instruments: list[str]) -> list[dict]:
        params = {"instruments": ",".join(instruments)}
        data = self._get("/pricing", params=params)
        return data.get("prices", [])

    def get_candles(
        self,
        instrument: str,
        granularity: str = "D",
        count: int = 500,
        from_time: datetime = None,
        to_time: datetime = None,
    ) -> list[dict]:
        params = {"granularity": granularity}

        if from_time:
            params["from"] = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if to_time:
            params["to"] = to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if count:
            params["count"] = count

        data = self._get(f"/instruments/{instrument}/candles", params=params)
        return data.get("candles", [])

    def create_order(self, order_body: dict) -> dict:
        data = self._post("/orders", body=order_body)
        return data

    def get_order(self, order_specifier: str) -> dict:
        data = self._get(f"/orders/{order_specifier}")
        return data

    def cancel_order(self, order_specifier: str) -> dict:
        data = self._put(f"/orders/{order_specifier}/cancel")
        return data

    def get_open_orders(self) -> list[dict]:
        data = self._get("/orders")
        return data.get("orders", [])

    def get_pending_orders(self) -> list[dict]:
        data = self._get("/orders?state=PENDING")
        return data.get("orders", [])

    def get_position(self, instrument: str) -> Optional[dict]:
        try:
            data = self._get(f"/positions/{instrument}")
            return data.get("position")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def get_open_positions(self) -> list[dict]:
        data = self._get("/openPositions")
        return data.get("positions", [])

    def get_open_trades(self) -> list[dict]:
        data = self._get("/trades")
        return data.get("trades", [])

    def get_transactions(self, from_time: datetime = None) -> list[dict]:
        params = {}
        if from_time:
            params["from"] = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = self._get("/transactions", params=params)
        return data.get("transactions", [])
