from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserLogin, AuthResponse
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, security
from pydantic import BaseModel

class RefreshRequest(BaseModel):
    refresh_token: str

router = APIRouter()

# Signup a new user
@router.post("/signup", response_model=AuthResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# Login a user
@router.post("/login", response_model=AuthResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# Refresh token
@router.post("/refresh", response_model=AuthResponse)
def refresh_token_endpoint(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = security.verify_token(req.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    email = payload.get("sub")
    user_id = payload.get("user_id")
    if not email or not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")
        
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User corresponding to token not found")
        
    access_token = create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    new_refresh_token = create_refresh_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
