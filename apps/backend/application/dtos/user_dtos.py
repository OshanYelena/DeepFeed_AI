"""
DeepFeed AI - Auth & User DTOs
Pydantic request/response models matching the TDS API design §7.3, §7.4, §7.5
"""
import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


# ── Auth DTOs ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Profile DTOs ──────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    expertise_level: str
    preferred_depth: str
    preferred_frequency: str
    updated_at: datetime


class UpdateProfileRequest(BaseModel):
    expertise_level: Optional[str] = None
    preferred_depth: Optional[str] = None
    preferred_frequency: Optional[str] = None

    @field_validator("expertise_level")
    @classmethod
    def validate_expertise(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("beginner", "intermediate", "advanced", "expert"):
            raise ValueError("expertise_level must be one of: beginner, intermediate, advanced, expert")
        return v

    @field_validator("preferred_depth")
    @classmethod
    def validate_depth(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("short", "medium", "deep"):
            raise ValueError("preferred_depth must be one of: short, medium, deep")
        return v

    @field_validator("preferred_frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("daily", "weekly", "realtime"):
            raise ValueError("preferred_frequency must be one of: daily, weekly, realtime")
        return v


# ── Interest DTOs ─────────────────────────────────────────────────────────────

class CreateInterestRequest(BaseModel):
    name: str
    description: Optional[str] = None
    weight: float = 0.5

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
        return v


class UpdateInterestRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = None

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
        return v


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    weight: float
    created_at: datetime


# ── User DTO ──────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime
