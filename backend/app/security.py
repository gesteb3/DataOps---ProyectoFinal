import hashlib
import os


def encrypt_password(password: str):

    secret = os.getenv(
        "PASSWORD_SECRET",
        "dataops_password_secret"
    )

    password_hash = hashlib.sha256(
        f"{password}{secret}".encode()
    ).hexdigest()

    return password_hash