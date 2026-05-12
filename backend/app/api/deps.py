"""Dependencies for API endpoints."""
from typing import Optional, Generator
from sqlalchemy.orm import Session
from fastapi import Depends

from ..database import get_db as get_db_session
from ..models import User
from ..core.auth import get_current_user as auth_get_current_user, User as AuthUser


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    yield from get_db_session()


async def get_current_user(
    auth_user: AuthUser = Depends(auth_get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the database.
    
    This combines JWT authentication with database lookup to ensure
    the user still exists in the database.
    """
    user = db.query(User).filter(User.id == auth_user.user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are an admin."""
    from fastapi import HTTPException, status
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
