from typing import Union

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from frontend.api import router as base_router
from auth.api import router as login_router
from config import api_settings

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
app.include_router(login_router)

app.mount("/static", StaticFiles(directory="frontend/BootStraps/startbootstrap/dist"), name="static")