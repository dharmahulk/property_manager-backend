"""
Common utility functions for the application.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from jose import jwt, JWTError

from config import api_settings


# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return hash_password(plain_password) == hashed_password


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=api_settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, api_settings.JWT_SECRET, algorithm=api_settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, api_settings.JWT_SECRET, algorithms=[api_settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def is_token_blocklisted(token: str) -> bool:
    """Check if a token is blocklisted"""
    return token in api_settings.TOKEN_BLOCKLIST


def add_to_blocklist(token: str) -> None:
    """Add a token to the blocklist"""
    api_settings.TOKEN_BLOCKLIST.add(token)