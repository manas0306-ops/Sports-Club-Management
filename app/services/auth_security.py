"""
Authentication & Cryptographic Security Engine
Native bcrypt hashing, signed session tokens, rate limiting, and audit logging.
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
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

# In-Memory Login Rate Limiting: key -> {"count": int, "lock_until": float}
_LOGIN_ATTEMPTS: Dict[str, Dict[str, Any]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with a random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")[:72] # Bcrypt max 72 bytes
    salt = bcrypt.gensalt(rounds=12)
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
    if not token:
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
