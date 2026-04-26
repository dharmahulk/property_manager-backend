from typing import Annotated, Union, Optional
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from users import models, schemas
from users.services import ListingService, PropertyService, UserService
from utils import decode_token, is_token_blocklisted
from config import api_settings, pg_sql_settings
from db import get_db


# Try to create database tables, but don't fail if database is not available
try:
    pg_sql_settings.db_base.metadata.create_all(bind=pg_sql_settings.db_engine)
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Database not available - {e}")
    DB_AVAILABLE = False


def get_db_session():
    if DB_AVAILABLE:
        yield from get_db()
    else:
        yield None


def get_current_user(
    authorization: Annotated[Optional[str], Header()],
    db: Union[Session, None] = Depends(get_db_session)
):
    """Dependency to get the current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    # Check if token is blocklisted
    if is_token_blocklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    if not DB_AVAILABLE or db is None:
        # Return mock user for demo mode
        return models.User(
            id=user_id,
            email="demo@example.com",
            name="Demo User",
            hashed_password="",
            phone_number=None,
            nri_status=False,
            location=None,
            owner_type=models.OwnerType.INDIVIDUAL,
            company_name=None,
            entity_type=None,
            tax_id=None,
            id_verification_status=models.IDVerificationStatus.NOT_SUBMITTED,
            is_active=True
        )
    
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


router = APIRouter(prefix="/listings", tags=["listings"])


def listing_to_response(listing_obj: models.RentalListing) -> dict:
    """Convert a RentalListing model to a response dict"""
    preferences = {}
    if listing_obj.preferences:
        try:
            preferences = json.loads(listing_obj.preferences)
        except (json.JSONDecodeError, TypeError):
            preferences = {}
    
    return {
        "id": listing_obj.id,
        "propertyId": listing_obj.property_id,
        "rent": listing_obj.rent,
        "securityDeposit": listing_obj.security_deposit,
        "maintenanceFee": listing_obj.maintenance_fee,
        "availableFrom": listing_obj.available_from.isoformat() if listing_obj.available_from else None,
        "status": listing_obj.status.value if hasattr(listing_obj.status, 'value') else listing_obj.status,
        "views": listing_obj.views,
        "enquiries": listing_obj.enquiries,
        "visits": listing_obj.visits,
        "preferences": preferences
    }


@router.get("", response_model=list[dict])
def get_listings(
    property_id: Optional[int] = Query(None, description="Filter by a specific property"),
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Get all rental listings belonging to the current user"""
    if not DB_AVAILABLE or db is None:
        # Demo mode - return empty list
        return []
    
    listings = ListingService.get_by_owner(db, current_user.id, property_id=property_id)
    return [listing_to_response(l) for l in listings]


@router.post("", response_model=dict, status_code=201)
def create_listing(
    listing_data: schemas.ListingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Create a new listing"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return {
            "id": 1,
            "propertyId": listing_data.property_id,
            "rent": listing_data.rent,
            "securityDeposit": listing_data.security_deposit,
            "maintenanceFee": listing_data.maintenance_fee,
            "availableFrom": listing_data.available_from,
            "status": listing_data.status,
            "views": 0,
            "enquiries": 0,
            "visits": 0,
            "preferences": listing_data.preferences.model_dump()
        }
    
    # Check if property exists and belongs to user
    property_obj = PropertyService.get_by_id(db, listing_data.property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="propertyId does not belong to the authenticated user")
    
    # Create listing
    listing_obj = ListingService.create(
        db,
        property_id=listing_data.property_id,
        rent=listing_data.rent,
        security_deposit=listing_data.security_deposit,
        maintenance_fee=listing_data.maintenance_fee,
        available_from=listing_data.available_from,
        status=listing_data.status,
        preferences=listing_data.preferences.model_dump()
    )
    
    return listing_to_response(listing_obj)


@router.get("/{listing_id}", response_model=dict)
def get_listing(
    listing_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Get a single listing by ID"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return {
            "id": listing_id,
            "propertyId": 1,
            "rent": 1000.0,
            "securityDeposit": 2000.0,
            "maintenanceFee": 100.0,
            "availableFrom": "2024-01-01",
            "status": "draft",
            "views": 0,
            "enquiries": 0,
            "visits": 0,
            "preferences": {
                "tenantType": "family",
                "foodPreference": "any",
                "petsAllowed": False,
                "minLeaseTerm": 12
            }
        }
    
    listing_obj = ListingService.get_by_id(db, listing_id)
    if not listing_obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check ownership through property
    property_obj = PropertyService.get_by_id(db, listing_obj.property_id)
    if not property_obj or property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return listing_to_response(listing_obj)


@router.patch("/{listing_id}", response_model=dict)
def update_listing(
    listing_id: int,
    listing_update: schemas.ListingUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Partially update a listing"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        update_data = listing_update.model_dump(exclude_unset=True)
        return {
            "id": listing_id,
            "propertyId": update_data.get("property_id", 1),
            "rent": update_data.get("rent", 1000.0),
            "securityDeposit": update_data.get("security_deposit", 2000.0),
            "maintenanceFee": update_data.get("maintenance_fee", 100.0),
            "availableFrom": update_data.get("available_from", "2024-01-01"),
            "status": update_data.get("status", "draft"),
            "views": 0,
            "enquiries": 0,
            "visits": 0,
            "preferences": update_data.get("preferences", {
                "tenantType": "family",
                "foodPreference": "any",
                "petsAllowed": False,
                "minLeaseTerm": 12
            })
        }
    
    listing_obj = ListingService.get_by_id(db, listing_id)
    if not listing_obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check ownership through property
    property_obj = PropertyService.get_by_id(db, listing_obj.property_id)
    if not property_obj or property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Update listing
    update_data = listing_update.model_dump(exclude_unset=True)
    listing_obj = ListingService.update(db, listing_id, **update_data)
    
    if not listing_obj:
        raise HTTPException(status_code=400, detail="Failed to update listing")
    
    return listing_to_response(listing_obj)


@router.delete("/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Delete a listing"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return None
    
    listing_obj = ListingService.get_by_id(db, listing_id)
    if not listing_obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Check ownership through property
    property_obj = PropertyService.get_by_id(db, listing_obj.property_id)
    if not property_obj or property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Delete listing
    ListingService.delete(db, listing_id)
    
    return None