from cryptography.fernet import Fernet

SECRET_KEY = "N0jP5q4h0a4X5xQ6vJ7J5J8yJ6g3L0P2dQ9Qx2fL1fE="
cipher = Fernet(SECRET_KEY.encode())

def encrypt_password(password: str):

    encrypted = cipher.encrypt(
        password.encode()
    )

    return encrypted.decode()