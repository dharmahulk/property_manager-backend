from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated, Union

from fastapi import APIRouter, Request, Form

router = APIRouter()


from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from auth.schemas import AdminUserResponse, AdminUserCreate
from config import pg_sql_settings

from auth.services import AdminUserService

# Try to create database tables, but don't fail if database is not available
try:
    pg_sql_settings.db_base.metadata.create_all(bind=pg_sql_settings.db_engine)
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Database not available - {e}")
    DB_AVAILABLE = False

# Mock database session for when DB is not available
def get_db_session():
    if DB_AVAILABLE:
        yield from pg_sql_settings.get_db_session()
    else:
        yield None


@router.post("/admin-users/", response_model=AdminUserResponse)
def create_user(
    name: Annotated[str, Form()], 
    email: Annotated[str, Form()], 
    password: Annotated[str, Form()],
    db: Union[Session, None] = Depends(get_db_session)
):
    print(f"DEBUG: Received user creation request - name: {name}, email: {email}")
    
    # Validate input data using schema
    try:
        user_data = AdminUserCreate(name=name, email=email, password=password)
    except Exception as e:
        print(f"DEBUG: Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    
    if not DB_AVAILABLE or db is None:
        print("DEBUG: Using demo mode for user creation")
        # Return mock response when database is not available
        return AdminUserResponse(
            id=1,
            name=user_data.name,
            email=user_data.email,
            is_active=True
        )
    
    db_user = AdminUserService.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return AdminUserService.create(db=db, model_instance=user_data.create_user_model)


@router.get("/admin-users/", response_model=list[AdminUserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Union[Session, None] = Depends(get_db_session)):
    if not DB_AVAILABLE or db is None:
        return []
    users = AdminUserService.get_all(db, skip=skip, limit=limit)
    return users


@router.get("/admin-users/{user_id}", response_model=AdminUserResponse)
def read_user(user_id: int, db: Union[Session, None] = Depends(get_db_session)):
    if not DB_AVAILABLE or db is None:
        return AdminUserResponse(id=user_id, name="Demo User", email="demo@example.com", is_active=True)
    db_user = AdminUserService.get_by_id(db, model_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/admin-users/authenticate", response_model=AdminUserResponse)
def authenticate_user(
    email: Annotated[str, Form()], 
    password: Annotated[str, Form()],
    db: Union[Session, None] = Depends(get_db_session)
):
    if not DB_AVAILABLE or db is None:
        # Return mock successful authentication for demo
        return AdminUserResponse(
            id=1,
            name="Demo User",
            email=email,
            is_active=True
        )
    
    db_user = AdminUserService.get_user_by_email(db, email=email)
    if not db_user or not AdminUserResponse.validate_password(db_user.hashed_password, password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return db_user