"""
Authentication & Cryptographic Security Engine
Native bcrypt hashing, signed session tokens, rate limiting, and audit logging.
"""
import time
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Set
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit import AuditLog

# Session Cookie Configuration
SESSION_COOKIE_NAME = "champions_session"
JWT_ALGORITHM = "HS256"
DEFAULT_SESSION_EXPIRE_HOURS = 24
REMEMBER_ME_EXPIRE_DAYS = 30

# In-Memory Token Revocation Blocklist
_REVOKED_TOKENS: Set[str] = set()

# In-Memory Password Reset Tokens: token -> {"user_id": int, "email": str, "expires_at": float, "used": bool}
_PASSWORD_RESET_TOKENS: Dict[str, Dict[str, Any]] = {}
RESET_TOKEN_EXPIRE_SECONDS = 900 # 15 minutes

# In-Memory Login Rate Limiting: key -> {"count": int, "lock_until": float}
_LOGIN_ATTEMPTS: Dict[str, Dict[str, Any]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60

def revoke_session_token(token: str) -> None:
    """Adds a session token to the revocation blocklist to invalidate it server-side."""
    if token:
        _REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    """Checks whether a session token has been revoked."""
    return bool(token and token in _REVOKED_TOKENS)

def create_password_reset_token(user_id: int, email: str) -> str:
    """Generates a secure, single-use, time-limited password reset token."""
    token = secrets.token_urlsafe(32)
    _PASSWORD_RESET_TOKENS[token] = {
        "user_id": user_id,
        "email": email.strip().lower(),
        "expires_at": time.time() + RESET_TOKEN_EXPIRE_SECONDS,
        "used": False
    }
    return token

def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates that a password reset token exists, is unexpired, and unused."""
    if not token:
        return None
    record = _PASSWORD_RESET_TOKENS.get(token)
    if not record:
        return None
    if record.get("used"):
        return None
    if time.time() > record.get("expires_at", 0):
        return None
    return record

def consume_password_reset_token(token: str) -> bool:
    """Marks a password reset token as consumed/used."""
    if token and token in _PASSWORD_RESET_TOKENS:
        _PASSWORD_RESET_TOKENS[token]["used"] = True
        return True
    return False

def hash_password(password: str, rounds: int = 12) -> str:
    """Hashes a plaintext password using bcrypt with a random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")[:72] # Bcrypt max 72 bytes
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash in constant time."""
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_session_token(
    user_id: int,
    username: str,
    primary_role: str,
    remember_me: bool = False
) -> str:
    """Creates a cryptographically signed JWT session token."""
    expire_duration = (
        timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
        if remember_me
        else timedelta(hours=DEFAULT_SESSION_EXPIRE_HOURS)
    )
    expire_time = datetime.utcnow() + expire_duration
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": primary_role,
        "exp": expire_time,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a session token. Returns payload or None."""
    if not token or is_token_revoked(token):
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def check_login_rate_limit(key: str) -> Tuple[bool, int]:
    """
    Checks if a login key (IP or username) is rate limited.
    Returns (is_locked, remaining_seconds).
    """
    now = time.time()
    record = _LOGIN_ATTEMPTS.get(key)
    if not record:
        return False, 0
    
    lock_until = record.get("lock_until", 0)
    if now < lock_until:
        return True, int(lock_until - now)
    elif lock_until > 0 and now >= lock_until:
        # Lockout expired, reset counter
        _LOGIN_ATTEMPTS[key] = {"count": 0, "lock_until": 0}
        return False, 0
    
    return False, 0

def record_login_failure(key: str) -> Tuple[bool, int]:
    """Records a failed attempt. Locks if max exceeded. Returns (is_locked, remaining_seconds)."""
    now = time.time()
    record = _LOGIN_ATTEMPTS.setdefault(key, {"count": 0, "lock_until": 0})
    record["count"] += 1
    
    if record["count"] >= MAX_FAILED_ATTEMPTS:
        record["lock_until"] = now + LOCKOUT_DURATION_SECONDS
        return True, LOCKOUT_DURATION_SECONDS
    return False, 0

def reset_login_attempts(key: str) -> None:
    """Clears failed login attempts upon successful authentication."""
    if key in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[key]

def log_security_event(
    db: Session,
    action: str,
    username: Optional[str] = None,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[str] = None
) -> AuditLog:
    """Persists a security or authorization event to the audit_logs table."""
    audit = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource=resource,
        ip_address=ip_address,
        status=status,
        details=details
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
