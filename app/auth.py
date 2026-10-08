from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings
from .models import User

# bcrypt 4.0.1 is pinned in requirements.txt because Passlib 1.7.4
# is not compatible with newer bcrypt releases.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer.")
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False

def create_access_token(uid: int, minutes: int = 1440) -> str:
    payload = {"sub": str(uid), "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def current_user(request, db):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        uid = int(payload["sub"])
        return db.get(User, uid)
    except (JWTError, KeyError, ValueError, TypeError):
        return None

def require_user(request, db):
    user = current_user(request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Login required")
    return user
