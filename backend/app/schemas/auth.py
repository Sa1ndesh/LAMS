from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import UserRoleEnum


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, json_schema_extra={"example": "Rajesh Sharma"})
    email: EmailStr = Field(..., json_schema_extra={"example": "user@lams.gov.in"})
    password: str = Field(..., min_length=6, max_length=100, json_schema_extra={"example": "SecurePass123!"})
    role: UserRoleEnum = Field(default=UserRoleEnum.VIEWER, json_schema_extra={"example": UserRoleEnum.VIEWER})
    state_id: Optional[int] = Field(default=None, json_schema_extra={"example": 1})
    district_id: Optional[int] = Field(default=None, json_schema_extra={"example": 1})


class UserLogin(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "admin.national@lams.gov.in"})
    password: str = Field(..., json_schema_extra={"example": "LamsAdmin@2026"})


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    state_id: Optional[int] = None
    district_id: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

