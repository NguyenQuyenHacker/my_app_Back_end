import uuid
from collections import Counter
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.enums import LedgerSide
from app.services.client import ledger_service, napas_mock, otp_service


def test_otp_roundtrip_matches():
    h = otp_service.hash_otp("123456")
    assert otp_service.verify_otp("123456", h) is True
    assert otp_service.verify_otp("000000", h) is False
    assert otp_service.verify_otp("", h) is False
    assert otp_service.verify_otp("123456", "") is False


def test_post_entry_rejects_zero_targets():
    session = MagicMock()
    with pytest.raises(ValueError):
        ledger_service.post_entry(
            session,
            transaction_id=uuid.uuid4(),
            entry_type=LedgerSide.DEBIT,
            amount=Decimal("10.00"),
        )


def test_post_entry_rejects_multiple_targets():
    session = MagicMock()
    with pytest.raises(ValueError):
        ledger_service.post_entry(
            session,
            transaction_id=uuid.uuid4(),
            entry_type=LedgerSide.DEBIT,
            amount=Decimal("10.00"),
            account_id=uuid.uuid4(),
            system_account_id=uuid.uuid4(),
        )


def test_post_entry_rejects_non_positive_amount():
    session = MagicMock()
    with pytest.raises(ValueError):
        ledger_service.post_entry(
            session,
            transaction_id=uuid.uuid4(),
            entry_type=LedgerSide.DEBIT,
            amount=Decimal("0"),
            account_id=uuid.uuid4(),
        )


def test_post_double_entry_creates_two_balanced_entries():
    session = MagicMock()
    txn_id = uuid.uuid4()
    src_id = uuid.uuid4()
    dst_id = uuid.uuid4()

    debit, credit = ledger_service.post_double_entry(
        session,
        transaction_id=txn_id,
        amount=Decimal("100.00"),
        debit={"account_id": src_id, "balance_after": Decimal("900.00")},
        credit={"account_id": dst_id, "balance_after": Decimal("1100.00")},
        description="test",
    )

    assert debit.entry_type == LedgerSide.DEBIT
    assert credit.entry_type == LedgerSide.CREDIT
    assert debit.amount == credit.amount == Decimal("100.00")
    assert debit.account_id == src_id
    assert credit.account_id == dst_id
    assert session.add.call_count == 2


def test_napas_mock_distribution_within_bounds(monkeypatch):
    monkeypatch.setattr(napas_mock.time, "sleep", lambda *_: None)
    counts = Counter()
    for _ in range(2000):
        r = napas_mock.send_to_napas(
            bank_code="BANK01",
            account_number="123",
            amount=Decimal("10"),
            simulate_delay=False,
        )
        counts[r["status"]] += 1
        assert r["ref_id"].startswith("NAPAS_")

    assert counts["SUCCESS"] > counts["FAILED"] > 0
    assert counts["SUCCESS"] + counts["FAILED"] + counts["TIMEOUT"] == 2000
