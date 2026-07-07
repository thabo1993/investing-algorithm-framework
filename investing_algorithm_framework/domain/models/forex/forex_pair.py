from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ForexPair:
    base: str
    quote: str

    @classmethod
    def from_symbol(cls, symbol: str) -> ForexPair:
        normalized = cls.normalize_symbol(symbol)
        parts = normalized.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid forex symbol: {symbol}. Expected format: BASE/QUOTE"
            )
        return cls(base=parts[0].upper(), quote=parts[1].upper())

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        cleaned = symbol.upper().strip()
        for sep in ("-", ".", "_", " "):
            if sep in cleaned:
                cleaned = cleaned.replace(sep, "/")
        if "/" not in cleaned and len(cleaned) == 6:
            cleaned = cleaned[:3] + "/" + cleaned[3:]
        return cleaned

    def to_oanda_format(self) -> str:
        return f"{self.base}_{self.quote}"

    @staticmethod
    def from_oanda_format(oanda_symbol: str) -> ForexPair:
        return ForexPair.from_symbol(oanda_symbol.replace("_", "/"))

    def to_yahoo_format(self) -> str:
        return f"{self.base}{self.quote}=X"

    def to_polygon_format(self) -> str:
        return f"C:{self.base}{self.quote}"

    def is_jpy_pair(self) -> bool:
        return self.quote == "JPY" or self.base == "JPY"

    def inverse_pair(self) -> ForexPair:
        return ForexPair(base=self.quote, quote=self.base)

    @property
    def pip_decimal_places(self) -> int:
        return 2 if self.is_jpy_pair() else 4

    @property
    def display_decimal_places(self) -> int:
        return 3 if self.is_jpy_pair() else 5

    def get_symbol(self) -> str:
        return f"{self.base}/{self.quote}"

    def __repr__(self) -> str:
        return f"ForexPair({self.base}/{self.quote})"
