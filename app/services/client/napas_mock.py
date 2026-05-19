import random
import time
import uuid
from typing import Optional

NAPAS_FAILURE_REASONS = [
    "DESTINATION_ACCOUNT_NOT_FOUND",
    "DESTINATION_BANK_REJECTED",
    "AMOUNT_LIMIT_EXCEEDED",
    "ACCOUNT_CLOSED",
]


def send_to_napas(
    *,
    bank_code: str,
    account_number: str,
    amount,
    description: Optional[str] = None,
    simulate_delay: bool = True,
) -> dict:
    if simulate_delay:
        time.sleep(random.uniform(1.0, 2.0))

    roll = random.random()
    ref_id = f"NAPAS_{uuid.uuid4().hex[:16].upper()}"

    if roll < 0.80:
        return {"status": "SUCCESS", "ref_id": ref_id, "reason": None}
    if roll < 0.95:
        return {
            "status": "FAILED",
            "ref_id": ref_id,
            "reason": random.choice(NAPAS_FAILURE_REASONS),
        }
    return {"status": "TIMEOUT", "ref_id": ref_id, "reason": "Upstream timeout"}
