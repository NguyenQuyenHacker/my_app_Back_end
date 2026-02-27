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