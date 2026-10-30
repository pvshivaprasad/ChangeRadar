"""Security utilities for ChangeRadar 1.0:
- Fernet symmetric encryption and decryption for sensitive GitHub tokens
- HMAC-SHA256 webhook signature verification
- Secret masking and sanitization
"""
import base64
import hashlib
import hmac
import os
import secrets
from typing import Optional
from cryptography.fernet import Fernet

from .config import settings

_FALLBACK_DEV_KEY = b"ChangeRadarDevMasterSecretKey2026=="  # 32 bytes base64 encoded


def _get_fernet_key() -> bytes:
    """Derives or validates a 32-byte urlsafe base64-encoded key for Fernet."""
    raw_key = settings.encryption_key
    if raw_key:
        try:
            # If already valid 32-byte base64 Fernet key
            decoded = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
            if len(decoded) == 32:
                return raw_key.encode("utf-8")
        except Exception:
            pass
        # Derive a 32-byte key using SHA-256
        derived = hashlib.sha256(raw_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(derived)

    if settings.environment == "production":
        raise ValueError("ENCRYPTION_KEY must be configured in production environment for secure token storage.")

    # Safe deterministic development fallback derived from app settings
    derived_dev = hashlib.sha256(b"changeradar-in-memory-dev-encryption-seed").digest()
    return base64.urlsafe_b64encode(derived_dev)


def encrypt_secret(plaintext: str) -> str:
    """Encrypts sensitive credentials (e.g. GitHub personal access tokens or OAuth tokens)."""
    if not plaintext:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypts ciphertext into plaintext credential."""
    if not ciphertext:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    try:
        decrypted = f.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as exc:
        raise ValueError(f"Failed to decrypt credential: {exc}")


def verify_github_webhook_signature(
    payload_bytes: bytes,
    signature_header: Optional[str],
    webhook_secret: str,
) -> bool:
    """
    Validates GitHub webhook delivery signature using HMAC-SHA256.
    Header format: 'sha256=<hex_digest>'
    Uses secrets.compare_digest to prevent timing attacks.
    """
    if not signature_header or not webhook_secret:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    actual_sig = signature_header[len("sha256="):].strip()
    return secrets.compare_digest(expected_sig, actual_sig)


def mask_token(token: Optional[str]) -> str:
    """Masks a token for user-facing API responses (e.g. 'ghp_****1234')."""
    if not token:
        return ""
    if len(token) <= 8:
        return "********"
    prefix = token[:4]
    suffix = token[-4:]
    return f"{prefix}****{suffix}"
