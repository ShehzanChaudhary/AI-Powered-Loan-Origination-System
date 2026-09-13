from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "LOAN_OFFICER" # only "LOAN_OFFICER" makes sense here - admins are bootstrapped, not registered

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

