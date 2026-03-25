from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class CurrentUserRead(BaseModel):
    userAccountId: str
    email: str
    roles: list[str]


class AuthResponse(BaseModel):
    accessToken: str
    tokenType: str = 'bearer'
    user: CurrentUserRead
