from datetime import datetime
from typing import Optional
import json

from sqlalchemy.orm import Session

from users import models
from utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    is_token_blocklisted,
    add_to_blocklist
)
from config import api_settings


# User Service
class UserService:
    model = models.User

    @classmethod
    def get_user_by_email(cls, db: Session, email: str):
        return db.query(cls.model).filter(cls.model.email == email).first()
    
    @classmethod
    def get_by_id(cls, db: Session, user_id: int):
        return db.query(cls.model).filter(cls.model.id == user_id).first()
    
    @classmethod
    def get_all(cls, db: Session, skip: int = 0, limit: int = 100):
        return db.query(cls.model).offset(skip).limit(limit).all()
    
    @classmethod
    def create(cls, db: Session, email: str, name: str, password: str, **kwargs):
        """Create a new user"""
        hashed_password = hash_password(password)
        user = cls.model(
            email=email,
            name=name,
            hashed_password=hashed_password,
            phone_number=kwargs.get("phone_number"),
            nri_status=kwargs.get("nri_status", False),
            location=kwargs.get("location"),
            owner_type=kwargs.get("owner_type", models.OwnerType.INDIVIDUAL),
            company_name=kwargs.get("company_name"),
            entity_type=kwargs.get("entity_type"),
            tax_id=kwargs.get("tax_id"),
            created_at=datetime.utcnow().isoformat()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @classmethod
    def update(cls, db: Session, user_id: int, **kwargs):
        """Update a user"""
        user = cls.get_by_id(db, user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str):
        """Authenticate a user by email and password"""
        user = cls.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


# Property Service
class PropertyService:
    model = models.Property

    @classmethod
    def get_by_id(cls, db: Session, property_id: int):
        return db.query(cls.model).filter(cls.model.id == property_id).first()
    
    @classmethod
    def get_by_owner(cls, db: Session, owner_id: int, skip: int = 0, limit: int = 100):
        return db.query(cls.model).filter(cls.model.owner_id == owner_id).offset(skip).limit(limit).all()
    
    @classmethod
    def create(cls, db: Session, owner_id: int, **kwargs):
        """Create a new property"""
        # Handle address as dict
        address = kwargs.pop("address", {})
        
        property = cls.model(
            owner_id=owner_id,
            digipin=kwargs.get("digipin"),
            nickname=kwargs.get("nickname"),
            type=models.PropertyType(kwargs.get("type")),
            size=kwargs.get("size"),
            size_unit=models.SizeUnit(kwargs.get("sizeUnit")),
            status=models.PropertyStatus(kwargs.get("status")),
            management_status=models.ManagementStatus(kwargs.get("managementStatus")),
            street=address.get("street"),
            city=address.get("city"),
            state=address.get("state"),
            zip=address.get("zip"),
            landmark=address.get("landmark"),
            images=json.dumps(kwargs.get("images", [])),
            rent=kwargs.get("rent"),
            tenant_name=kwargs.get("tenant_name"),
            lease_expiry=kwargs.get("lease_expiry"),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(property)
        db.commit()
        db.refresh(property)
        return property
    
    @classmethod
    def update(cls, db: Session, property_id: int, **kwargs):
        """Update a property"""
        property = cls.get_by_id(db, property_id)
        if not property:
            return None
        
        # Handle address update
        if "address" in kwargs and kwargs["address"]:
            address = kwargs.pop("address")
            for key, value in address.items():
                if hasattr(property, key):
                    setattr(property, key, value)
        
        # Handle images
        if "images" in kwargs:
            kwargs["images"] = json.dumps(kwargs["images"])
        
        # Handle enum conversions
        for key in ["type", "sizeUnit", "status", "managementStatus"]:
            if key in kwargs and kwargs[key]:
                if key == "type":
                    kwargs[key] = models.PropertyType(kwargs[key])
                elif key == "sizeUnit":
                    kwargs[key] = models.SizeUnit(kwargs[key])
                elif key == "status":
                    kwargs[key] = models.PropertyStatus(kwargs[key])
                elif key == "managementStatus":
                    kwargs[key] = models.ManagementStatus(kwargs[key])
        
        for key, value in kwargs.items():
            if value is not None and hasattr(property, key):
                setattr(property, key, value)
        
        property.updated_at = datetime.utcnow().isoformat()
        db.commit()
        db.refresh(property)
        return property
    
    @classmethod
    def delete(cls, db: Session, property_id: int):
        """Delete a property"""
        property = cls.get_by_id(db, property_id)
        if not property:
            return False
        db.delete(property)
        db.commit()
        return True


# Listing Service
class ListingService:
    model = models.RentalListing

    @classmethod
    def get_by_id(cls, db: Session, listing_id: int):
        return db.query(cls.model).filter(cls.model.id == listing_id).first()
    
    @classmethod
    def get_by_property(cls, db: Session, property_id: int, skip: int = 0, limit: int = 100):
        return db.query(cls.model).filter(cls.model.property_id == property_id).offset(skip).limit(limit).all()
    
    @classmethod
    def get_by_owner(cls, db: Session, owner_id: int, property_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get all listings for properties owned by the user"""
        query = db.query(cls.model).join(models.Property).filter(models.Property.owner_id == owner_id)
        if property_id:
            query = query.filter(cls.model.property_id == property_id)
        return query.offset(skip).limit(limit).all()
    
    @classmethod
    def create(cls, db: Session, **kwargs):
        """Create a new listing"""
        preferences = kwargs.pop("preferences", {})
        
        listing = cls.model(
            property_id=kwargs.get("property_id"),
            rent=kwargs.get("rent"),
            security_deposit=kwargs.get("security_deposit"),
            maintenance_fee=kwargs.get("maintenance_fee"),
            available_from=kwargs.get("available_from"),
            status=models.ListingStatus(kwargs.get("status")),
            preferences=json.dumps(preferences),
            views=0,
            enquiries=0,
            visits=0,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        return listing
    
    @classmethod
    def update(cls, db: Session, listing_id: int, **kwargs):
        """Update a listing"""
        listing = cls.get_by_id(db, listing_id)
        if not listing:
            return None
        
        # Handle preferences update
        if "preferences" in kwargs and kwargs["preferences"]:
            kwargs["preferences"] = json.dumps(kwargs["preferences"])
        
        # Handle status enum
        if "status" in kwargs and kwargs["status"]:
            kwargs["status"] = models.ListingStatus(kwargs["status"])
        
        for key, value in kwargs.items():
            if value is not None and hasattr(listing, key):
                setattr(listing, key, value)
        
        listing.updated_at = datetime.utcnow().isoformat()
        db.commit()
        db.refresh(listing)
        return listing
    
    @classmethod
    def delete(cls, db: Session, listing_id: int):
        """Delete a listing"""
        listing = cls.get_by_id(db, listing_id)
        if not listing:
            return False
        db.delete(listing)
        db.commit()
        return True