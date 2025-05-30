# app/models.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class RoleEnum(str, Enum):
    client = "client"
    ops = "ops"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum

class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: RoleEnum

class TokenData(BaseModel):
    email: Optional[str] = None

class FileOut(BaseModel):
    id: str
    filename: str
    uploaded_by: str
