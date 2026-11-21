import base64, hashlib, hmac, os, secrets
from pathlib import Path
import bcrypt as native
from passlib.hash import bcrypt

def password_hash(value):
    if native.__version__.startswith("5."):
        return native.hashpw(value.encode(), native.gensalt()).decode()
    return bcrypt.hash(value)

def password_ok(value, hashed):
    if len(value.encode()) > 72: return False
    if native.__version__.startswith("5."):
        return native.checkpw(value.encode(), hashed.encode())
    return bcrypt.verify(value, hashed)

def secret():
    if os.getenv("SESSION_SECRET"): return os.environ["SESSION_SECRET"]
    path=Path(".club-secret")
    try:
        with path.open("x") as f: f.write(secrets.token_hex(32))
    except FileExistsError: pass
    return path.read_text().strip()
SECRET=secret()
try:
    from itsdangerous import URLSafeSerializer, BadSignature
    serializer=URLSafeSerializer(SECRET,salt="club-session")
except ImportError:
    serializer=None

def sign(value):
    if serializer: return serializer.dumps(value)
    return value+"."+hmac.new(SECRET.encode(),value.encode(),"sha256").hexdigest()

def unsign(value):
    if serializer:
        try: return serializer.loads(value)
        except BadSignature: return ""
    raw=value.rpartition(".")[0]
    return raw if hmac.compare_digest(sign(raw),value) else ""

def digest(value): return hashlib.sha256(value.encode()).hexdigest()
