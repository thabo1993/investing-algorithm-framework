import os

from investing_algorithm_framework.domain.exceptions import \
    OperationalException

from .market_credential import MarketCredential


class FxcmCredential(MarketCredential):
    """
    FXCM market credential. ForexConnect authenticates with
    username/password/connection(Demo|Real)/host_url instead of
    api_key/secret_key.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        connection: str = "Demo",
        host_url: str = None,
        market: str = "FXCM",
    ):
        super().__init__(market=market)
        self._username = username
        self._password = password
        self._connection = connection
        self._host_url = host_url

    def initialize(self):
        # ponytail: dedicated FXCM env vars; override base initialize()
        # which requires api_key. FXCM auth needs
        # username/password/connection/host_url.
        self._username = self._username or os.getenv("FXCM_USERNAME")
        self._password = self._password or os.getenv("FXCM_PASSWORD")
        self._connection = os.getenv("FXCM_CONNECTION", self._connection)
        self._host_url = self._host_url or os.getenv("FXCM_URL")

        if not self._username or not self._password:
            raise OperationalException(
                "FXCM credential requires a username and password, either as "
                "arguments or as FXCM_USERNAME / FXCM_PASSWORD environment "
                "variables (connection: FXCM_CONNECTION, host: FXCM_URL)."
            )

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def connection(self):
        return self._connection

    @property
    def host_url(self):
        return self._host_url

    def __repr__(self):
        return f"FxcmCredential({self.market}, {self.username}, " \
               f"{self.connection}, {self.host_url})"
