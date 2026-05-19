import enum


class GenderType(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class CardStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class TransferType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class LedgerSide(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class ExternalBankAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class SystemAccountCode(str, enum.Enum):
    SUSPENSE = "SUSPENSE"
    CLEARING = "CLEARING"