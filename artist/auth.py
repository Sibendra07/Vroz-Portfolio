from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import os

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from pymongo import MongoClient
from core.db import collection_tokens as tokens_collection

load_dotenv()

# Router setup
router = APIRouter(prefix="/auth", tags=["auth"])

# Configuration
SECRET_KEY = "cLBXZ1yXcS3qBUqZF9PXn436Kg7kVFpN2xjgi2lz1Qg" # Ensure this is a long, random string in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$KZvW8kPYFeQfuhC8YDayTOUr2kWBOAJk7dKiaXy.Of.uXcmifFblu")

# Password tools
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class AdminUser(BaseModel):
    username: str

# Dependency to get MongoDB collection
def get_tokens_collection():
    return tokens_collection

# Authentication functions
def verify_admin(username: str, password: str):
    """Verify if credentials match the admin user"""
    if username != ADMIN_USERNAME:
        return False
    return pwd_context.verify(password, ADMIN_PASSWORD_HASH)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token and store it in MongoDB"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != ADMIN_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return AdminUser(username=ADMIN_USERNAME)

# Routes
@router.post("/token", response_model=Token)
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
):
    """Login endpoint that returns a JWT token"""
    if not verify_admin(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": ADMIN_USERNAME},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    tokens_collection = Depends(get_tokens_collection)
):
    """Logout endpoint to delete the current token"""
    token = credentials.credentials
    result = tokens_collection.delete_one({"token": token})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token not found"
        )
    
    return {"message": "Successfully logged out"}

@router.get("/dashboard")
async def admin_dashboard(current_admin: AdminUser = Depends(get_current_admin)):
    """Protected admin dashboard"""
    return {"message": f"Welcome to the admin dashboard, {current_admin.username}!"}