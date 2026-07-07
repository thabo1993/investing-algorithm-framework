from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class MarginUtilizationResult:
    margin_used: Decimal
    margin_available: Decimal
    utilization_percentage: float
    leverage: int
    is_margin_call: bool


def calculate_margin_utilization(
    position_notional: Decimal,
    account_balance: Decimal,
    leverage: int = 30,
) -> MarginUtilizationResult:
    if leverage <= 0:
        raise ValueError("Leverage must be positive")

    margin_rate = Decimal("1") / Decimal(str(leverage))
    margin_used = (position_notional * margin_rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    margin_available = (account_balance - margin_used).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if account_balance > 0:
        utilization_pct = float(
            (margin_used / account_balance * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )
    else:
        utilization_pct = 0.0

    is_margin_call = (
        account_balance > 0 and margin_used >= account_balance
    )

    return MarginUtilizationResult(
        margin_used=margin_used,
        margin_available=margin_available,
        utilization_percentage=utilization_pct,
        leverage=leverage,
        is_margin_call=is_margin_call,
    )
