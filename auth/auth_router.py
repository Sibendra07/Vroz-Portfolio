from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from auth.auth_model import Token, AdminUser
from auth.auth_service import verify_admin, create_access_token
from core.config import config
from core.deps import get_tokens_collection, get_current_admin


# Router setup
router = APIRouter(prefix="/auth", tags=["auth"])

bearer_scheme = HTTPBearer()



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
        data={"sub": config.ADMIN_USERNAME},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
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