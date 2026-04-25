from typing import Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from auth import models
from fastapi import UploadFile, File, Form

class AdminUserBase(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    name: str = Field(..., min_length=1, description="Full name")

    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(AdminUserBase):
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")

    @property
    def create_user_model(self):
        fake_hashed_password = self.password + "notreallyhashed"
        user = models.AdminUser(
            email=self.email, 
            hashed_password=fake_hashed_password,
            name=self.name,
            is_active=True  # Set default value
        )
        return user


class AdminUserResponse(AdminUserBase):
    id: int
    is_active: bool

    @staticmethod
    def validate_password(hashed_password, password):
        return hashed_password == password + "notreallyhashed"

    model_config = ConfigDict(from_attributes=True)