"""
Cryptographic utilities for sensitive data encryption.

SECURITY NOTICE:
- Uses Fernet (symmetric encryption) from cryptography library
- Requires ENCRYPTION_KEY in environment
- Never log decrypted values
- Used for Aadhaar last-4 digits encryption
"""
import logging
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def get_fernet_instance():
    """
    Get Fernet instance with encryption key from settings.
    
    Raises:
        ImproperlyConfigured: If ENCRYPTION_KEY is not set
    """
    encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if not encryption_key:
        raise ImproperlyConfigured(
            "ENCRYPTION_KEY not found in settings. "
            "Please set ENCRYPTION_KEY in your .env file. "
            "Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Ensure key is bytes
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
    
    return Fernet(encryption_key)


def encrypt_value(plain_text: str) -> bytes:
    """
    Encrypt a plain text value using Fernet.
    
    Args:
        plain_text: The text to encrypt
        
    Returns:
        Encrypted bytes
        
    Security:
        - Never logs the plain_text value
        - Returns binary data suitable for BinaryField
    """
    if not plain_text:
        return None
    
    fernet = get_fernet_instance()
    
    # Convert to bytes if needed
    if isinstance(plain_text, str):
        plain_text = plain_text.encode()
    
    encrypted = fernet.encrypt(plain_text)
    logger.debug("Value encrypted successfully (length: %d bytes)", len(encrypted))
    
    return encrypted


def decrypt_value(cipher_bytes: bytes) -> str:
    """
    Decrypt encrypted bytes back to plain text.
    
    Args:
        cipher_bytes: The encrypted bytes to decrypt
        
    Returns:
        Decrypted string
        
    Security:
        - Never logs the decrypted value
        - Use only when necessary
    """
    if not cipher_bytes:
        return None
    
    fernet = get_fernet_instance()
    
    decrypted = fernet.decrypt(cipher_bytes)
    logger.debug("Value decrypted successfully")
    
    return decrypted.decode()
