from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from users import models


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1)
    phone_number: Optional[str] = None
    nri_status: bool = False
    location: Optional[str] = None
    owner_type: str = "individual"
    company_name: Optional[str] = None
    entity_type: Optional[str] = None
    tax_id: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    nri_status: Optional[bool] = None
    location: Optional[str] = None
    owner_type: Optional[str] = None
    company_name: Optional[str] = None
    entity_type: Optional[str] = None
    tax_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    id: int
    id_verification_status: str = "not_submitted"

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


# Property Schemas
class AddressSchema(BaseModel):
    street: str
    city: str
    state: str
    zip: str
    landmark: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyBase(BaseModel):
    digipin: str
    nickname: str
    type: str  # residential, commercial, land
    size: float
    sizeUnit: str  # sqft, sqm
    status: str  # vacant, occupied, maintenance
    managementStatus: str  # active, onboarding, maintenance
    address: AddressSchema
    images: Optional[List[str]] = []
    rent: Optional[float] = None
    tenant_name: Optional[str] = None
    lease_expiry: Optional[str] = None  # ISO date string

    model_config = ConfigDict(from_attributes=True)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    digipin: Optional[str] = None
    nickname: Optional[str] = None
    type: Optional[str] = None
    size: Optional[float] = None
    sizeUnit: Optional[str] = None
    status: Optional[str] = None
    managementStatus: Optional[str] = None
    address: Optional[AddressSchema] = None
    images: Optional[List[str]] = None
    rent: Optional[float] = None
    tenant_name: Optional[str] = None
    lease_expiry: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyResponse(PropertyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Listing Schemas
class PreferencesSchema(BaseModel):
    tenant_type: str  # family, bachelors, any
    food_preference: str  # veg, non-veg, any
    pets_allowed: bool
    min_lease_term: int  # months

    model_config = ConfigDict(from_attributes=True)


class ListingBase(BaseModel):
    property_id: int
    rent: float
    security_deposit: float
    maintenance_fee: float
    available_from: str  # ISO date
    status: str  # draft, published, under_negotiation, leased
    preferences: PreferencesSchema

    model_config = ConfigDict(from_attributes=True)


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    property_id: Optional[int] = None
    rent: Optional[float] = None
    security_deposit: Optional[float] = None
    maintenance_fee: Optional[float] = None
    available_from: Optional[str] = None
    status: Optional[str] = None
    preferences: Optional[PreferencesSchema] = None

    model_config = ConfigDict(from_attributes=True)


class ListingResponse(ListingBase):
    id: int
    views: int = 0
    enquiries: int = 0
    visits: int = 0

    model_config = ConfigDict(from_attributes=True)


# Error Response
class ErrorResponse(BaseModel):
    message: str
    code: Optional[str] = None