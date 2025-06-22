from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
import os

from app.models.user import UserCreate, UserResponse
from app.utils.security import create_access_token, verify_token
from app.services.auth_service import AuthService
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
auth_service = AuthService()

# filepath: c:\Users\DELL\OneDrive\Desktop\dbpro\quantum-dashboard-backend\app\routers\auth.py
@router.post("/register")
async def register(user_data: UserCreate):
    try:
        user = await auth_service.create_user(user_data)
        access_token_expires = timedelta(minutes=int(os.getenv("JWT_EXPIRE_MINUTES", 30)))
        token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
        return {
            "token": token,
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("JWT_EXPIRE_MINUTES", 30)))
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return TokenResponse(access_token=token, token_type="bearer")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    payload = verify_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await auth_service.get_current_user(payload["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
