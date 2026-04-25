from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Float, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from config import pg_sql_settings


class OwnerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class IDVerificationStatus(str, enum.Enum):
    NOT_SUBMITTED = "not_submitted"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REJECTED = "rejected"


class User(pg_sql_settings.db_base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    nri_status = Column(Boolean, default=False)
    location = Column(String, nullable=True)
    owner_type = Column(SQLEnum(OwnerType), default=OwnerType.INDIVIDUAL)
    company_name = Column(String, nullable=True)
    entity_type = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    id_verification_status = Column(SQLEnum(IDVerificationStatus), default=IDVerificationStatus.NOT_SUBMITTED)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, nullable=True)  # ISO format timestamp
    
    # Relationships
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")


class PropertyType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"


class PropertyStatus(str, enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class ManagementStatus(str, enum.Enum):
    ACTIVE = "active"
    ONBOARDING = "onboarding"
    MAINTENANCE = "maintenance"


class SizeUnit(str, enum.Enum):
    SQFT = "sqft"
    SQM = "sqm"


class Property(pg_sql_settings.db_base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    digipin = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    type = Column(SQLEnum(PropertyType), nullable=False)
    size = Column(Float, nullable=False)
    size_unit = Column(SQLEnum(SizeUnit), nullable=False)
    status = Column(SQLEnum(PropertyStatus), nullable=False)
    management_status = Column(SQLEnum(ManagementStatus), nullable=False)
    
    # Address fields
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip = Column(String, nullable=False)
    landmark = Column(String, nullable=True)
    
    # Additional fields
    images = Column(String, nullable=True)  # JSON string of URLs
    rent = Column(Float, nullable=True)
    tenant_name = Column(String, nullable=True)
    lease_expiry = Column(Date, nullable=True)
    
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="properties")
    listings = relationship("RentalListing", back_populates="property", cascade="all, delete-orphan")


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNDER_NEGOTIATION = "under_negotiation"
    LEASED = "leased"


class TenantType(str, enum.Enum):
    FAMILY = "family"
    BACHELORS = "bachelors"
    ANY = "any"


class FoodPreference(str, enum.Enum):
    VEG = "veg"
    NON_VEG = "non-veg"
    ANY = "any"


class RentalListing(pg_sql_settings.db_base):
    __tablename__ = "rental_listings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    rent = Column(Float, nullable=False)
    security_deposit = Column(Float, nullable=False)
    maintenance_fee = Column(Float, nullable=False)
    available_from = Column(Date, nullable=False)
    status = Column(SQLEnum(ListingStatus), nullable=False)
    views = Column(Integer, default=0)
    enquiries = Column(Integer, default=0)
    visits = Column(Integer, default=0)
    
    # Preferences (stored as JSON string)
    preferences = Column(String, nullable=True)
    
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="listings")