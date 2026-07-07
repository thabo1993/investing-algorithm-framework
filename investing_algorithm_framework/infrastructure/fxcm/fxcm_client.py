import os
import logging
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("investing_algorithm_framework")

# Sidecar connection is read from the modern process environment. FXCM broker
# credentials never live here (research D8) — they live only in the sidecar's
# own environment. The modern process only knows how to reach the sidecar.
FXCM_SIDECAR_HOST_ENV = "FXCM_SIDECAR_HOST"
FXCM_SIDECAR_PORT_ENV = "FXCM_SIDECAR_PORT"
FXCM_SIDECAR_TOKEN_ENV = "FXCM_SIDECAR_TOKEN"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = "8787"


class FxcmSidecarError(Exception):
    """Raised when the sidecar returns a non-2xx {"error":{code,message}}."""

    def __init__(self, code: str, message: str, status_code: int = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class FxcmClient:
    """
    Localhost IPC client to the FXCM sidecar (research D1/D3;
    contracts/fxcm-sidecar-ipc.md). HTTP request/response for candles/account/
    positions/orders, plus a WebSocket consumer for the live tick stream.

    This is the FXCM analogue of the reference broker client, but the transport is the
    loopback sidecar (which is the sole holder of ForexConnect + FXCM
    credentials), not a public broker REST API. Auth is the shared
    X-Sidecar-Token header (research D8).
    """

    def __init__(
        self,
        host: str = None,
        port=None,
        token: str = None,
        timeout: int = 10,
    ):
        self.host = host or os.getenv(FXCM_SIDECAR_HOST_ENV, DEFAULT_HOST)
        self.port = str(port or os.getenv(FXCM_SIDECAR_PORT_ENV, DEFAULT_PORT))
        self.token = token or os.getenv(FXCM_SIDECAR_TOKEN_ENV, "")
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}"
        self.ws_url = f"ws://{self.host}:{self.port}/stream"

        self._session = requests.Session()
        if self.token:
            self._session.headers.update({"X-Sidecar-Token": self.token})

    # ── HTTP request/response ───────────────────────────────────

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        response = self._session.request(
            method, url, timeout=self.timeout, **kwargs
        )

        if response.status_code >= 400:
            try:
                err = response.json().get("error", {})
            except ValueError:
                err = {}
            raise FxcmSidecarError(
                code=err.get("code", "SIDECAR_ERROR"),
                message=err.get("message", response.text),
                status_code=response.status_code,
            )

        return response.json()

    def get_health(self) -> dict:
        return self._request("GET", "/health")

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        from_time: datetime = None,
        to_time: datetime = None,
        count: int = None,
    ) -> list:
        params = {"symbol": symbol, "timeframe": timeframe}
        if from_time is not None:
            params["start"] = _iso(from_time)
        if to_time is not None:
            params["end"] = _iso(to_time)
        if count is not None:
            params["count"] = count

        data = self._request("GET", "/candles", params=params)
        return data.get("candles", [])

    def get_account(self) -> dict:
        return self._request("GET", "/account")

    def get_positions(self) -> list:
        data = self._request("GET", "/positions")
        return data.get("positions", [])

    def create_order(self, order_body: dict) -> dict:
        return self._request("POST", "/orders", json=order_body)

    def cancel_order(self, external_id: str) -> dict:
        return self._request("DELETE", f"/orders/{external_id}")

    # ── WebSocket live stream (sidecar → backend) ───────────────

    async def stream(self):
        """
        Async generator yielding parsed sidecar events
        (price|position|account|session). Consumed by the BFF WS fan-out
        (later task). websockets is imported lazily so HTTP-only callers
        (e.g. FxcmOHLCVDataProvider) don't require it.
        """
        import json
        import websockets

        headers = (
            {"X-Sidecar-Token": self.token} if self.token else {}
        )
        async with websockets.connect(
            self.ws_url, additional_headers=headers
        ) as ws:
            async for raw in ws:
                yield json.loads(raw)
