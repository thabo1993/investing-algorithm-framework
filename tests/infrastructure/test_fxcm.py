import sys
import unittest
from unittest.mock import patch

from investing_algorithm_framework.domain import OperationalException
from investing_algorithm_framework.domain.models.market.fxcm_credential \
    import FxcmCredential
from investing_algorithm_framework.infrastructure.fxcm.fxcm_client import (
    _load_forexconnect,
    _fxcm_instrument,
)


class TestFxcmCredential(unittest.TestCase):

    def test_init_with_arguments(self):
        credential = FxcmCredential(
            username="user",
            password="pass",
            connection="Real",
            host_url="https://example.com/Hosts.jsp",
        )
        credential.initialize()
        self.assertEqual(credential.market, "FXCM")
        self.assertEqual(credential.username, "user")
        self.assertEqual(credential.password, "pass")
        self.assertEqual(credential.connection, "Real")
        self.assertEqual(
            credential.host_url, "https://example.com/Hosts.jsp"
        )

    def test_connection_defaults_to_demo(self):
        credential = FxcmCredential(username="user", password="pass")
        self.assertEqual(credential.connection, "Demo")

    @patch.dict(
        "os.environ",
        {
            "FXCM_USERNAME": "env_user",
            "FXCM_PASSWORD": "env_pass",
            "FXCM_CONNECTION": "Real",
            "FXCM_URL": "https://env.example.com/Hosts.jsp",
        },
    )
    def test_initialize_from_env_vars(self):
        credential = FxcmCredential()
        credential.initialize()
        self.assertEqual(credential.username, "env_user")
        self.assertEqual(credential.password, "env_pass")
        self.assertEqual(credential.connection, "Real")
        self.assertEqual(
            credential.host_url, "https://env.example.com/Hosts.jsp"
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_initialize_missing_username_raises(self):
        credential = FxcmCredential(password="pass")
        with self.assertRaises(OperationalException) as ctx:
            credential.initialize()
        self.assertIn("FXCM_USERNAME", str(ctx.exception))

    @patch.dict("os.environ", {}, clear=True)
    def test_initialize_missing_password_raises(self):
        credential = FxcmCredential(username="user")
        with self.assertRaises(OperationalException) as ctx:
            credential.initialize()
        self.assertIn("FXCM_PASSWORD", str(ctx.exception))


class TestLoadForexconnect(unittest.TestCase):
    """US3: SDK absent -> actionable OperationalException (NFR-004)."""

    def test_missing_sdk_raises_operational_exception(self):
        # Force the import to fail even if forexconnect were installed.
        with patch.dict(sys.modules, {"forexconnect": None}):
            with self.assertRaises(OperationalException) as ctx:
                _load_forexconnect()

        message = str(ctx.exception)
        self.assertIn("forexconnect", message)
        self.assertIn("investing-algorithm-framework[fxcm]", message)
        self.assertIn("3.14", message)
        self.assertNotIsInstance(ctx.exception, ModuleNotFoundError)

    def test_error_chains_original_import_error(self):
        with patch.dict(sys.modules, {"forexconnect": None}):
            with self.assertRaises(OperationalException) as ctx:
                _load_forexconnect()
        self.assertIsInstance(ctx.exception.__cause__, ImportError)


class TestFxcmInstrument(unittest.TestCase):

    def test_passthrough_uppercase_strip(self):
        self.assertEqual(_fxcm_instrument(" eur/usd "), "EUR/USD")
        self.assertEqual(_fxcm_instrument("EUR/USD"), "EUR/USD")


if __name__ == "__main__":
    unittest.main()
