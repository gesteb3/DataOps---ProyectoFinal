import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def _get_password_secret() -> str:
    return os.getenv("PASSWORD_SECRET", "dataops_password_secret")


def _get_fernet() -> Fernet:
    secret = _get_password_secret().encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_password(password: str) -> str:
    return _get_fernet().encrypt(password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted_password.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "La contraseña guardada no se puede descifrar. "
            "Este registro posiblemente fue creado con la versión anterior "
            "que usaba hash SHA256 no reversible. Registra nuevamente el motor "
            "o prueba la conexión usando POST /connections/test."
        ) from exc
