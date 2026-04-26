from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import engine
from config import pg_sql_settings

from frontend.api import router as base_router
from auth.api import router as login_router
from properties.api import router as properties_router
from listings.api import router as listings_router
from users.api import router as users_router
from config import api_settings
from images.api import router as images_router
app = FastAPI(
    title=api_settings.PROJECT_NAME,
    description="Modern FastAPI Application with Authentication",
    version="1.0.0",
    openapi_url=f"{api_settings.API_STR}/openapi.json",
    docs_url="/docs" if api_settings.HOST_DOCS else None,
    redoc_url="/redoc" if api_settings.HOST_DOCS else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def on_startup():
    pg_sql_settings.db_base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

# Test routes for debugging
@app.get("/test")
async def serve_test_page():
    return FileResponse("test_user_creation.html")

@app.get("/debug")
async def serve_debug_page():
    return FileResponse("debug_signup.html")

app.include_router(base_router)
app.include_router(login_router, prefix=api_settings.API_STR)
app.include_router(properties_router, prefix=api_settings.API_STR)
app.include_router(listings_router, prefix=api_settings.API_STR)
app.include_router(users_router, prefix=api_settings.API_STR)
app.include_router(images_router, prefix=api_settings.API_STR)


from starlette.middleware.sessions import SessionMiddleware


# Add session middleware for authentication
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here-change-in-production")
