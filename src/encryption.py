"""
Модуль шифрования для безопасного хранения паролей
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Уникальный ключ для проекта (генерируется один раз)
# Хранится в файле .encryption_key
KEY_FILE = ".encryption_key"


def get_or_create_key() -> bytes:
    """Получить или создать ключ шифрования"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        # Скрываем файл (Windows)
        try:
            os.system(f'attrib +h {KEY_FILE}')
        except Exception:
            pass
        return key


def encrypt_password(password: str) -> str:
    """Шифрование пароля"""
    if not password:
        return ""
    
    key = get_or_create_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted).decode('utf-8')


def decrypt_password(encrypted_password: str) -> str:
    """Расшифровка пароля"""
    if not encrypted_password:
        return ""
    
    try:
        key = get_or_create_key()
        f = Fernet(key)
        # Декодируем из base64
        encrypted = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))
        decrypted = f.decrypt(encrypted)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Ошибка расшифровки: {e}")
        return ""


def encrypt_field(data: str) -> str:
    """Шифрование поля (пароль или ключ)"""
    return encrypt_password(data)


def decrypt_field(encrypted_data: str) -> str:
    """Расшифровка поля"""
    return decrypt_password(encrypted_data)
