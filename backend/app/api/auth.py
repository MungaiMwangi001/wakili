"""
Authentication endpoints:
  POST /auth/register  – Create a new user account
  POST /auth/login     – Authenticate and receive JWT
  GET  /auth/me        – Return current user profile
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.utils.auth_deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Normalize email to lowercase
    email = data.email.strip().lower()
    
    # Check if user exists with normalized email
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,  # Use normalized email
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
        preferred_language=data.preferred_language or "en",
    )
    
    db.add(user)
    await db.commit()  # IMPORTANT: Commit to save to database
    await db.refresh(user)  # Refresh to get the generated ID
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Normalize email to lowercase for lookup
    email = data.email.strip().lower()
    
    # Query with normalized email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Debug logging (remove after fixing)
    print(f"Login attempt - Email: '{email}'")
    print(f"User found: {user is not None}")
    if user:
        print(f"Stored email: '{user.email}'")
        print(f"Password verified: {verify_password(data.password, user.hashed_password)}")

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user