from decimal import Decimal

import pytest

from app.services.client.savings_service import (
    _calc_interest_early,
    _calc_interest_full_term,
    _q,
)


def test_quantize_rounds_half_up():
    assert _q(Decimal("1.005")) == Decimal("1.01")
    assert _q(Decimal("1.004")) == Decimal("1.00")


def test_full_term_interest_basic():
    # 100tr * 6%/năm * 12 tháng = 6tr
    interest = _calc_interest_full_term(Decimal("100000000"), Decimal("0.06"), 12)
    assert interest == Decimal("6000000.00")


def test_full_term_interest_six_months():
    # 100tr * 6%/năm * 6 tháng = 3tr
    interest = _calc_interest_full_term(Decimal("100000000"), Decimal("0.06"), 6)
    assert interest == Decimal("3000000.00")


def test_full_term_interest_one_month():
    interest = _calc_interest_full_term(Decimal("12000000"), Decimal("0.05"), 1)
    # 12.000.000 * 0.05 / 12 = 50.000
    assert interest == Decimal("50000.00")


def test_full_term_interest_rounding():
    # 1.234.567 * 0.0420 * 3 / 12 = 12.962,9535 -> 12962.95
    interest = _calc_interest_full_term(Decimal("1234567"), Decimal("0.0420"), 3)
    assert interest == Decimal("12962.95")


def test_early_interest_zero_days():
    assert _calc_interest_early(Decimal("100000000"), Decimal("0.001"), 0) == Decimal("0.00")


def test_early_interest_negative_days_is_zero():
    assert _calc_interest_early(Decimal("100000000"), Decimal("0.001"), -3) == Decimal("0.00")


def test_early_interest_30_days():
    # 100tr * 0.001 * 30 / 365 ~= 8.219,1780
    interest = _calc_interest_early(Decimal("100000000"), Decimal("0.001"), 30)
    assert interest == Decimal("8219.18")


def test_early_interest_365_days():
    # 100tr * 0.001 * 365 / 365 = 100.000
    interest = _calc_interest_early(Decimal("100000000"), Decimal("0.001"), 365)
    assert interest == Decimal("100000.00")


@pytest.mark.parametrize("principal,rate,months,expected", [
    (Decimal("50000000"), Decimal("0.0350"), 1, Decimal("145833.33")),
    (Decimal("50000000"), Decimal("0.0510"), 6, Decimal("1275000.00")),
    (Decimal("50000000"), Decimal("0.0580"), 12, Decimal("2900000.00")),
])
def test_full_term_interest_table(principal, rate, months, expected):
    assert _calc_interest_full_term(principal, rate, months) == expected
