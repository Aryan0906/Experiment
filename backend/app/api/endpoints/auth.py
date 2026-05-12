"""
Authentication endpoints for Google OAuth and JWT token management.
"""
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from ..database import get_db
from ..models import User
from ..core.auth import create_access_token

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


class GoogleLoginRequest(BaseModel):
    """Request body for Google login."""
    credential: str  # Google ID token from frontend


class TokenResponse(BaseModel):
    """Response with JWT token and user info."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str | None = None
    avatar_url: str | None = None


@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth and return a JWT token.
    
    The frontend sends the Google ID token obtained from @react-oauth/google.
    We verify it with Google and then issue our own JWT token.
    
    Args:
        request: Google credential token
        db: Database session
        
    Returns:
        JWT token and user info
        
    Raises:
        HTTPException: If Google token is invalid or user not found/created
    """
    if not GOOGLE_CLIENT_ID:
        # Development mode - accept any token
        # In production, this should be disabled
        print("[WARNING] GOOGLE_CLIENT_ID not set, using development mode")
        # For dev, we'll create a mock user
        email = "dev@example.com"
        name = "Dev User"
        google_id = "dev_google_id"
        avatar_url = None
    else:
        # Verify Google token
        try:
            idinfo = id_token.verify_oauth2_token(
                request.credential,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
            
            email = idinfo.get("email")
            name = idinfo.get("name")
            google_id = idinfo.get("sub")
            avatar_url = idinfo.get("picture")
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google token: no email"
                )
                
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )
    
    # Find or create user in database
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url,
            is_admin=False  # Set to True manually in DB for admin users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[AUTH] Created new user: {email} (ID: {user.id})")
    else:
        # Update existing user info
        user.name = name
        user.avatar_url = avatar_url
        db.commit()
        print(f"[AUTH] Logged in existing user: {email} (ID: {user.id})")
    
    # Create JWT token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "is_admin": user.is_admin
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url
    )


@router.get("/me")
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Will be overridden by auth
):
    """
    Get current authenticated user info.
    
    This endpoint requires authentication via Bearer token.
    """
    from ..core.auth import get_current_user as auth_get_current_user
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Depends
    
    security = HTTPBearer()
    credentials: HTTPAuthorizationCredentials = Depends(security)
    
    # This is a simplified version - in practice use the deps.get_current_user
    user_data = auth_get_current_user.__call__(credentials)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "is_admin": user.is_admin
    }
