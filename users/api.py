from typing import List, Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from config import api_settings
from db import get_db
from utils import is_token_blocklisted, decode_token, add_to_blocklist, create_access_token
from users import schemas, services, models


# OAuth2 scheme

# Router
router = APIRouter(prefix="/api/users", tags=["users"])


# Dependency to get current user
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get the current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Check if token is blocklisted
    if is_token_blocklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = services.UserService.get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Auth Endpoints
@router.post("/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = services.UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = services.UserService.create(
        db,
        email=user_data.email,
        name=user_data.name,
        password=user_data.password,
        phone_number=user_data.phone_number,
        nri_status=user_data.nri_status,
        location=user_data.location,
        owner_type=models.OwnerType(user_data.owner_type) if user_data.owner_type else models.OwnerType.INDIVIDUAL,
        company_name=user_data.company_name,
        entity_type=user_data.entity_type,
        tax_id=user_data.tax_id
    )
    
    # Create token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "userId": user.id},
        expires_delta=timedelta(minutes=api_settings.JWT_EXPIRE_MINUTES)
    )
    
    return schemas.TokenResponse(
        token=access_token,
        user=schemas.UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone_number=user.phone_number,
            nri_status=user.nri_status,
            location=user.location,
            owner_type=user.owner_type.value if user.owner_type else "individual",
            company_name=user.company_name,
            entity_type=user.entity_type,
            tax_id=user.tax_id,
            id_verification_status=user.id_verification_status.value if user.id_verification_status else "not_submitted"
        )
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = services.UserService.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "userId": user.id},
        expires_delta=timedelta(minutes=api_settings.JWT_EXPIRE_MINUTES)
    )
    
    return schemas.TokenResponse(
        token=access_token,
        user=schemas.UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone_number=user.phone_number,
            nri_status=user.nri_status,
            location=user.location,
            owner_type=user.owner_type.value if user.owner_type else "individual",
            company_name=user.company_name,
            entity_type=user.entity_type,
            tax_id=user.tax_id,
            id_verification_status=user.id_verification_status.value if user.id_verification_status else "not_submitted"
        )
    )


@router.post("/logout", response_model=schemas.LogoutResponse)
def logout(authorization: str = Header(None)):
    """Logout by adding token to blocklist"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
        add_to_blocklist(token)
    
    return schemas.LogoutResponse()


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current user profile"""
    return schemas.UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone_number=current_user.phone_number,
        nri_status=current_user.nri_status,
        location=current_user.location,
        owner_type=current_user.owner_type.value if current_user.owner_type else "individual",
        company_name=current_user.company_name,
        entity_type=current_user.entity_type,
        tax_id=current_user.tax_id,
        id_verification_status=current_user.id_verification_status.value if current_user.id_verification_status else "not_submitted"
    )


@router.patch("/me", response_model=schemas.UserResponse)
def patch_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle owner_type conversion
    if "owner_type" in update_data and update_data["owner_type"]:
        update_data["owner_type"] = models.OwnerType(update_data["owner_type"])
    
    user = services.UserService.update(db, current_user.id, **update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return schemas.UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone_number=user.phone_number,
        nri_status=user.nri_status,
        location=user.location,
        owner_type=user.owner_type.value if user.owner_type else "individual",
        company_name=user.company_name,
        entity_type=user.entity_type,
        tax_id=user.tax_id,
        id_verification_status=user.id_verification_status.value if user.id_verification_status else "not_submitted"
    )


# Property Endpoints
@router.get("/properties", response_model=List[schemas.PropertyResponse])
def get_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties for the current user"""
    properties = services.PropertyService.get_by_owner(db, current_user.id, skip, limit)
    
    result = []
    for prop in properties:
        images = []
        if prop.images:
            try:
                images = json.loads(prop.images) if isinstance(prop.images, str) else prop.images
            except:
                images = []
        
        result.append(schemas.PropertyResponse(
            id=prop.id,
            digipin=prop.digipin,
            nickname=prop.nickname,
            type=prop.type.value if prop.type else "residential",
            size=prop.size,
            sizeUnit=prop.size_unit.value if prop.size_unit else "sqft",
            status=prop.status.value if prop.status else "vacant",
            managementStatus=prop.management_status.value if prop.management_status else "active",
            address=schemas.AddressSchema(
                street=prop.street,
                city=prop.city,
                state=prop.state,
                zip=prop.zip,
                landmark=prop.landmark
            ),
            images=images,
            rent=prop.rent,
            tenant_name=prop.tenant_name,
            lease_expiry=prop.lease_expiry.isoformat() if prop.lease_expiry else None
        ))
    
    return result


@router.post("/properties", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: schemas.PropertyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property"""
    property = services.PropertyService.create(
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
    
    return schemas.PropertyResponse(
        id=property.id,
        digipin=property.digipin,
        nickname=property.nickname,
        type=property.type.value if property.type else "residential",
        size=property.size,
        sizeUnit=property.size_unit.value if property.size_unit else "sqft",
        status=property.status.value if property.status else "vacant",
        managementStatus=property.management_status.value if property.management_status else "active",
        address=schemas.AddressSchema(
            street=property.street,
            city=property.city,
            state=property.state,
            zip=property.zip,
            landmark=property.landmark
        ),
        images=property_data.images,
        rent=property.rent,
        tenant_name=property.tenant_name,
        lease_expiry=property.lease_expiry
    )


@router.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific property"""
    property = services.PropertyService.get_by_id(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Verify ownership
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this property"
        )
    
    images = []
    if property.images:
        try:
            images = json.loads(property.images) if isinstance(property.images, str) else property.images
        except:
            images = []
    
    return schemas.PropertyResponse(
        id=property.id,
        digipin=property.digipin,
        nickname=property.nickname,
        type=property.type.value if property.type else "residential",
        size=property.size,
        sizeUnit=property.size_unit.value if property.size_unit else "sqft",
        status=property.status.value if property.status else "vacant",
        managementStatus=property.management_status.value if property.management_status else "active",
        address=schemas.AddressSchema(
            street=property.street,
            city=property.city,
            state=property.state,
            zip=property.zip,
            landmark=property.landmark
        ),
        images=images,
        rent=property.rent,
        tenant_name=property.tenant_name,
        lease_expiry=property.lease_expiry.isoformat() if property.lease_expiry else None
    )


@router.patch("/properties/{property_id}", response_model=schemas.PropertyResponse)
def update_property(
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a property"""
    property = services.PropertyService.get_by_id(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Verify ownership
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this property"
        )
    
    update_data = property_update.model_dump(exclude_unset=True)
    
    # Handle address update
    if "address" in update_data and update_data["address"]:
        update_data["address"] = update_data["address"].model_dump()
    
    property = services.PropertyService.update(db, property_id, **update_data)
    
    images = []
    if property.images:
        try:
            images = json.loads(property.images) if isinstance(property.images, str) else property.images
        except:
            images = []
    
    return schemas.PropertyResponse(
        id=property.id,
        digipin=property.digipin,
        nickname=property.nickname,
        type=property.type.value if property.type else "residential",
        size=property.size,
        sizeUnit=property.size_unit.value if property.size_unit else "sqft",
        status=property.status.value if property.status else "vacant",
        managementStatus=property.management_status.value if property.management_status else "active",
        address=schemas.AddressSchema(
            street=property.street,
            city=property.city,
            state=property.state,
            zip=property.zip,
            landmark=property.landmark
        ),
        images=images,
        rent=property.rent,
        tenant_name=property.tenant_name,
        lease_expiry=property.lease_expiry.isoformat() if property.lease_expiry else None
    )


@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a property"""
    property = services.PropertyService.get_by_id(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Verify ownership
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this property"
        )
    
    services.PropertyService.delete(db, property_id)
    return None


# Listing Endpoints
@router.get("/listings", response_model=List[schemas.ListingResponse])
def get_listings(
    property_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all listings for the current user"""
    listings = services.ListingService.get_by_owner(db, current_user.id, property_id, skip, limit)
    
    result = []
    for listing in listings:
        preferences = {}
        if listing.preferences:
            try:
                preferences = json.loads(listing.preferences) if isinstance(listing.preferences, str) else listing.preferences
            except:
                preferences = {}
        
        result.append(schemas.ListingResponse(
            id=listing.id,
            property_id=listing.property_id,
            rent=listing.rent,
            security_deposit=listing.security_deposit,
            maintenance_fee=listing.maintenance_fee,
            available_from=listing.available_from.isoformat() if listing.available_from else "",
            status=listing.status.value if listing.status else "draft",
            preferences=schemas.PreferencesSchema(**preferences) if preferences else schemas.PreferencesSchema(
                tenant_type="any",
                food_preference="any",
                pets_allowed=False,
                min_lease_term=12
            ),
            views=listing.views,
            enquiries=listing.enquiries,
            visits=listing.visits
        ))
    
    return result


@router.post("/listings", response_model=schemas.ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: schemas.ListingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new listing"""
    # Verify property ownership
    property = services.PropertyService.get_by_id(db, listing_data.property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create listing for this property"
        )
    
    listing = services.ListingService.create(
        db,
        property_id=listing_data.property_id,
        rent=listing_data.rent,
        security_deposit=listing_data.security_deposit,
        maintenance_fee=listing_data.maintenance_fee,
        available_from=listing_data.available_from,
        status=listing_data.status,
        preferences=listing_data.preferences.model_dump()
    )
    
    return schemas.ListingResponse(
        id=listing.id,
        property_id=listing.property_id,
        rent=listing.rent,
        security_deposit=listing.security_deposit,
        maintenance_fee=listing.maintenance_fee,
        available_from=listing.available_from.isoformat() if listing.available_from else "",
        status=listing.status.value if listing.status else "draft",
        preferences=listing_data.preferences,
        views=listing.views,
        enquiries=listing.enquiries,
        visits=listing.visits
    )


@router.get("/listings/{listing_id}", response_model=schemas.ListingResponse)
def get_listing(
    listing_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific listing"""
    listing = services.ListingService.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Verify ownership through property
    property = services.PropertyService.get_by_id(db, listing.property_id)
    if not property or property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this listing"
        )
    
    preferences = {}
    if listing.preferences:
        try:
            preferences = json.loads(listing.preferences) if isinstance(listing.preferences, str) else listing.preferences
        except:
            preferences = {}
    
    return schemas.ListingResponse(
        id=listing.id,
        property_id=listing.property_id,
        rent=listing.rent,
        security_deposit=listing.security_deposit,
        maintenance_fee=listing.maintenance_fee,
        available_from=listing.available_from.isoformat() if listing.available_from else "",
        status=listing.status.value if listing.status else "draft",
        preferences=schemas.PreferencesSchema(**preferences) if preferences else schemas.PreferencesSchema(
            tenant_type="any",
            food_preference="any",
            pets_allowed=False,
            min_lease_term=12
        ),
        views=listing.views,
        enquiries=listing.enquiries,
        visits=listing.visits
    )


@router.patch("/listings/{listing_id}", response_model=schemas.ListingResponse)
def update_listing(
    listing_id: int,
    listing_update: schemas.ListingUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a listing"""
    listing = services.ListingService.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Verify ownership through property
    property = services.PropertyService.get_by_id(db, listing.property_id)
    if not property or property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this listing"
        )
    
    update_data = listing_update.model_dump(exclude_unset=True)
    
    # Handle preferences update
    if "preferences" in update_data and update_data["preferences"]:
        update_data["preferences"] = update_data["preferences"].model_dump()
    
    listing = services.ListingService.update(db, listing_id, **update_data)
    
    preferences = {}
    if listing.preferences:
        try:
            preferences = json.loads(listing.preferences) if isinstance(listing.preferences, str) else listing.preferences
        except:
            preferences = {}
    
    return schemas.ListingResponse(
        id=listing.id,
        property_id=listing.property_id,
        rent=listing.rent,
        security_deposit=listing.security_deposit,
        maintenance_fee=listing.maintenance_fee,
        available_from=listing.available_from.isoformat() if listing.available_from else "",
        status=listing.status.value if listing.status else "draft",
        preferences=schemas.PreferencesSchema(**preferences) if preferences else schemas.PreferencesSchema(
            tenant_type="any",
            food_preference="any",
            pets_allowed=False,
            min_lease_term=12
        ),
        views=listing.views,
        enquiries=listing.enquiries,
        visits=listing.visits
    )


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a listing"""
    listing = services.ListingService.get_by_id(db, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Verify ownership through property
    property = services.PropertyService.get_by_id(db, listing.property_id)
    if not property or property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this listing"
        )
    
    services.ListingService.delete(db, listing_id)
    return None


# Import json for JSON parsing
import json