from pydantic import BaseModel, EmailStr, ConfigDict

# User create schema
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# User login schema
class UserLogin(BaseModel):
    username: str
    password: str

# User response schema
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

# Auth response schema
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Token data schema
class TokenData(BaseModel):
    email: str
    user_id: str
