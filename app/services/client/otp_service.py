from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_otp(raw_otp: str, otp_hash: str) -> bool:
    if not raw_otp or not otp_hash:
        return False
    try:
        return _pwd_context.verify(raw_otp, otp_hash)
    except Exception:
        return False


def hash_otp(raw_otp: str) -> str:
    return _pwd_context.hash(raw_otp)
