import enum

class GenderType(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class AccountType(str, enum.Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    TERM = "TERM"

class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"

class CardType(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    VIRTUAL = "VIRTUAL"

class CardStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class TransferType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    INTERBANK = "INTERBANK"

class TransferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_OTP = "PENDING_OTP"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class BillStatus(str, enum.Enum):
    DUE = "DUE"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
