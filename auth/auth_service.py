from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta

from core.config import config
from core.deps import get_tokens_collection


# Password tools
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_admin(username: str, password: str):
    """Verify if credentials match the admin user"""
    if username != config.ADMIN_USERNAME:
        return False
    return pwd_context.verify(password, config.ADMIN_PASSWORD_HASH)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token and store it in MongoDB"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    
    # Store token in MongoDB
    tokens_collection = get_tokens_collection()
    token_data = {
        "token": token,
        "username": data["sub"],
        "expires_at": expire,
        "created_at": datetime.utcnow()
    }
    tokens_collection.insert_one(token_data)
    
    return token