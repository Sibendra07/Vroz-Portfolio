from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status

from auth.auth_model import AdminUser
from core.config import config
from core.db import collection_tokens as tokens_collection

# Auth module
def get_tokens_collection():
    return tokens_collection


# Authentication functions
bearer_scheme = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    tokens_collection = Depends(get_tokens_collection)
):
    """Validate token and return admin user if valid"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    try:
        # Check if token exists in MongoDB
        token_data = tokens_collection.find_one({"token": token})
        if not token_data:
            raise credentials_exception
        
        # Verify JWT
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username != config.ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return AdminUser(username=config.ADMIN_USERNAME)