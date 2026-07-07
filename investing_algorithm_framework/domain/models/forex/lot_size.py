from enum import Enum
from decimal import Decimal


class LotSize(Enum):
    STANDARD = 100000
    MINI = 10000
    MICRO = 1000

    @classmethod
    def from_units(cls, units: int) -> "LotSize":
        for lot in cls:
            if lot.value == units:
                return lot
        raise ValueError(
            f"No LotSize matches {units} units. "
            f"Use STANDARD ({cls.STANDARD.value}), "
            f"MINI ({cls.MINI.value}), or "
            f"MICRO ({cls.MICRO.value})."
        )

    def to_units(self) -> int:
        return self.value

    def to_decimal(self) -> Decimal:
        return Decimal(str(self.value))

    def __repr__(self) -> str:
        return f"{self.name} ({self.value} units)"
