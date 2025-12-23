"""
Cryptographic utilities for secure credential storage.

Uses Fernet symmetric encryption for storing sensitive data like API keys and OAuth tokens.
"""

import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Module-level cipher instance (initialized lazily)
_cipher: Optional[Fernet] = None


def _get_cipher() -> Fernet:
    """Get or create the Fernet cipher instance."""
    global _cipher
    if _cipher is None:
        from app.config import get_settings
        settings = get_settings()

        key = settings.encryption_key
        if not key:
            # Generate a key for development (not recommended for production)
            if settings.is_development:
                key = Fernet.generate_key().decode()
                logger.warning(
                    "No ENCRYPTION_KEY set, using generated key. "
                    "Set ENCRYPTION_KEY environment variable for production!"
                )
            else:
                raise ValueError(
                    "ENCRYPTION_KEY must be set in production. "
                    "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )

        # Ensure key is properly formatted
        try:
            _cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.error(f"Invalid encryption key format: {e}")
            raise ValueError(
                "Invalid ENCRYPTION_KEY format. Must be a valid Fernet key (32 bytes, base64 encoded)."
            )

    return _cipher


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a credential for secure storage.

    Args:
        plaintext: The credential to encrypt

    Returns:
        Base64-encoded encrypted string
    """
    if not plaintext:
        return ""

    cipher = _get_cipher()
    encrypted = cipher.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_credential(ciphertext: str) -> str:
    """
    Decrypt a stored credential.

    Args:
        ciphertext: The encrypted credential

    Returns:
        Decrypted plaintext string

    Raises:
        ValueError: If decryption fails (invalid token or corrupted data)
    """
    if not ciphertext:
        return ""

    cipher = _get_cipher()
    try:
        decrypted = cipher.decrypt(ciphertext.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.error("Failed to decrypt credential - invalid token or wrong key")
        raise ValueError("Failed to decrypt credential. The encryption key may have changed.")
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise ValueError(f"Failed to decrypt credential: {e}")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted (Fernet format).

    Fernet tokens start with 'gAAA' when base64 encoded.
    """
    if not value:
        return False
    return value.startswith("gAAA")


def encrypt_if_needed(value: str) -> str:
    """
    Encrypt a value only if it's not already encrypted.

    Args:
        value: The value to encrypt

    Returns:
        Encrypted value
    """
    if not value or is_encrypted(value):
        return value
    return encrypt_credential(value)


def decrypt_if_needed(value: str) -> str:
    """
    Decrypt a value only if it appears to be encrypted.

    Args:
        value: The value to decrypt

    Returns:
        Decrypted value, or original if not encrypted
    """
    if not value or not is_encrypted(value):
        return value
    try:
        return decrypt_credential(value)
    except ValueError:
        # Return original value if decryption fails (might be plaintext)
        logger.warning("Decryption failed, returning original value")
        return value


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded key string suitable for ENCRYPTION_KEY env var
    """
    return Fernet.generate_key().decode()
