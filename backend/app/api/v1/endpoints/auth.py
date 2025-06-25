from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}