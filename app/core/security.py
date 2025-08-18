from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

def _get_cipher() -> Fernet:
    key = settings.ENCRYPTION_KEY
    # Accept raw 32-byte urlsafe base64 key or derive from string
    if len(key) != 44 or not key.endswith("="):
        # Derive deterministic 32-byte base64 key from provided string (not cryptographically ideal; replace with KMS in prod)
        import base64, hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest())
    return Fernet(key)

def encrypt_blob(data: bytes) -> bytes:
    return _get_cipher().encrypt(data)

def decrypt_blob(token: bytes) -> bytes:
    return _get_cipher().decrypt(token)

# Convenience helpers and safe-decryption utilities

def encrypt_text(text: str) -> bytes:
    return encrypt_blob(text.encode())

def decrypt_text(token: bytes) -> str:
    return decrypt_blob(token).decode()

def try_decrypt_text(token: bytes | None) -> str | None:
    """
    Attempt to decrypt an encrypted text blob, returning None if decryption fails.
    """
    if not token:
        return None
    try:
        return decrypt_text(token)
    except InvalidToken:
        return None
    except Exception:
        return None

def redact_token(value: str | None, show: int = 4) -> str:
    """
    Redact sensitive token strings for logging. Keeps last N chars.
    """
    if not value:
        return ""
    if len(value) <= show:
        return "*" * len(value)
    return "*" * (len(value) - show) + value[-show:]
