from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.core.security import security
from app.models.user import User
from app.schemas.user import TokenData

security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.verify_token(credentials.credentials, "access")
        if payload is None:
            raise credentials_exception
            
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not isinstance(email, str) or not isinstance(user_id, str):
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    # Update last login
    setattr(user, 'last_login', datetime.utcnow())
    db.commit()
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
