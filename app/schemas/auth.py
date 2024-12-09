from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: int | None = None


class Login(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True


class UserAuth(UserBase):
    id: int
    is_superadmin: bool

    class Config:
        from_attributes = True
