from typing import Annotated, Union, Optional
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from auth import models, schemas
from auth.services import PropertyService, UserService, decode_token, is_token_blocklisted
from config import api_settings, pg_sql_settings


# Try to create database tables, but don't fail if database is not available
try:
    pg_sql_settings.db_base.metadata.create_all(bind=pg_sql_settings.db_engine)
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Database not available - {e}")
    DB_AVAILABLE = False


def get_db_session():
    if DB_AVAILABLE:
        yield from pg_sql_settings.get_db_session()
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


router = APIRouter(prefix="/properties", tags=["properties"])


def property_to_response(property_obj: models.Property) -> dict:
    """Convert a Property model to a response dict"""
    images = []
    if property_obj.images:
        try:
            images = json.loads(property_obj.images)
        except (json.JSONDecodeError, TypeError):
            images = []
    
    return {
        "id": property_obj.id,
        "digipin": property_obj.digipin,
        "nickname": property_obj.nickname,
        "type": property_obj.type.value if hasattr(property_obj.type, 'value') else property_obj.type,
        "size": property_obj.size,
        "sizeUnit": property_obj.size_unit.value if hasattr(property_obj.size_unit, 'value') else property_obj.size_unit,
        "status": property_obj.status.value if hasattr(property_obj.status, 'value') else property_obj.status,
        "managementStatus": property_obj.management_status.value if hasattr(property_obj.management_status, 'value') else property_obj.management_status,
        "address": {
            "street": property_obj.street,
            "city": property_obj.city,
            "state": property_obj.state,
            "zip": property_obj.zip,
            "landmark": property_obj.landmark
        },
        "images": images,
        "rent": property_obj.rent,
        "tenantName": property_obj.tenant_name,
        "leaseExpiry": property_obj.lease_expiry.isoformat() if property_obj.lease_expiry else None
    }


@router.get("", response_model=list[dict])
def get_properties(
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Get all properties belonging to the current user"""
    if not DB_AVAILABLE or db is None:
        # Demo mode - return empty list
        return []
    
    properties = PropertyService.get_by_owner(db, current_user.id)
    return [property_to_response(p) for p in properties]


@router.post("", response_model=dict, status_code=201)
def create_property(
    property_data: schemas.PropertyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Create a new property"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return {
            "id": 1,
            "digipin": property_data.digipin,
            "nickname": property_data.nickname,
            "type": property_data.type,
            "size": property_data.size,
            "sizeUnit": property_data.sizeUnit,
            "status": property_data.status,
            "managementStatus": property_data.managementStatus,
            "address": property_data.address.model_dump(),
            "images": property_data.images,
            "rent": property_data.rent,
            "tenantName": property_data.tenant_name,
            "leaseExpiry": property_data.lease_expiry
        }
    
    # Create property
    property_obj = PropertyService.create(
        db,
        owner_id=current_user.id,
        digipin=property_data.digipin,
        nickname=property_data.nickname,
        type=property_data.type,
        size=property_data.size,
        sizeUnit=property_data.sizeUnit,
        status=property_data.status,
        managementStatus=property_data.managementStatus,
        address=property_data.address.model_dump(),
        images=property_data.images,
        rent=property_data.rent,
        tenant_name=property_data.tenant_name,
        lease_expiry=property_data.lease_expiry
    )
    
    return property_to_response(property_obj)


@router.get("/{property_id}", response_model=dict)
def get_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Get a single property by ID"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return {
            "id": property_id,
            "digipin": "DEMO123",
            "nickname": "Demo Property",
            "type": "residential",
            "size": 1000.0,
            "sizeUnit": "sqft",
            "status": "vacant",
            "managementStatus": "active",
            "address": {
                "street": "123 Demo St",
                "city": "Demo City",
                "state": "Demo State",
                "zip": "12345",
                "landmark": None
            },
            "images": [],
            "rent": None,
            "tenantName": None,
            "leaseExpiry": None
        }
    
    property_obj = PropertyService.get_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check ownership
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Property belongs to a different user")
    
    return property_to_response(property_obj)


@router.patch("/{property_id}", response_model=dict)
def update_property(
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Partially update a property"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        update_data = property_update.model_dump(exclude_unset=True)
        return {
            "id": property_id,
            "digipin": update_data.get("digipin", "DEMO123"),
            "nickname": update_data.get("nickname", "Demo Property"),
            "type": update_data.get("type", "residential"),
            "size": update_data.get("size", 1000.0),
            "sizeUnit": update_data.get("sizeUnit", "sqft"),
            "status": update_data.get("status", "vacant"),
            "managementStatus": update_data.get("managementStatus", "active"),
            "address": update_data.get("address", {
                "street": "123 Demo St",
                "city": "Demo City",
                "state": "Demo State",
                "zip": "12345",
                "landmark": None
            }),
            "images": update_data.get("images", []),
            "rent": update_data.get("rent"),
            "tenantName": update_data.get("tenant_name"),
            "leaseExpiry": update_data.get("lease_expiry")
        }
    
    property_obj = PropertyService.get_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check ownership
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Update property
    update_data = property_update.model_dump(exclude_unset=True)
    property_obj = PropertyService.update(db, property_id, **update_data)
    
    if not property_obj:
        raise HTTPException(status_code=400, detail="Failed to update property")
    
    return property_to_response(property_obj)


@router.delete("/{property_id}", status_code=204)
def delete_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Union[Session, None] = Depends(get_db_session)
):
    """Delete a property (and cascade-delete its listings)"""
    if not DB_AVAILABLE or db is None:
        # Demo mode
        return None
    
    property_obj = PropertyService.get_by_id(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check ownership
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Delete property (cascade deletes listings)
    PropertyService.delete(db, property_id)
    
    return None