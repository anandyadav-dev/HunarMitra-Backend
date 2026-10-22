import os
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine
from app.models.base_class import Base
from app.api.v1.api import api_router
from app.seed_admin_and_data import seed_database

# Ensure uploads directory exists prior to mounting StaticFiles
os.makedirs("uploads/work_proofs", exist_ok=True)

# Initialize database tables automatically on launch
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
    seed_database()
except Exception as e:
    print(f"Warning: Could not connect to DB or create tables automatically: {e}")
    print("Please verify your MySQL service status and DATABASE_URL connection parameter.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Hunar Mitra (Customers) and Hunar Mitra Partner (Workers) marketplace.",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS for cross-origin mobile app or frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve worker work proof uploads statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include the unified V1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level direct routes for GET /wallet, GET /config/coins, coin packs, payments, and worker reveal/contact APIs
from app.api.v1.endpoints import (
    wallet as wallet_endpoint,
    config as config_endpoint,
    customer as customer_endpoint,
    coin_packs as coin_packs_endpoint,
    payments as payments_endpoint,
    admin as admin_endpoint,
    feedback as feedback_endpoint,
    auth as auth_endpoint
)
app.include_router(auth_endpoint.router, prefix="/auth", tags=["Authentication (Direct)"])
app.include_router(wallet_endpoint.router, tags=["Wallet & Coins (Direct)"])
app.include_router(config_endpoint.router, tags=["Configuration (Direct)"])
app.include_router(customer_endpoint.router, tags=["Customer Operations (Direct)"])
app.include_router(coin_packs_endpoint.router, tags=["Coin Packs & Orders (Direct)"])
app.include_router(payments_endpoint.router, tags=["Payments & Webhooks (Direct)"])
app.include_router(admin_endpoint.router, tags=["Admin Operations (Direct)"])
app.include_router(feedback_endpoint.router, tags=["Feedback & Reviews (Direct)"])

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Format the error message to be human readable
    error_msg = "Validation Error"
    if errors:
        first_error = errors[0]
        loc = " -> ".join([str(l) for l in first_error.get("loc", [])])
        msg = first_error.get("msg", "")
        error_msg = f"{loc}: {msg}"
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": error_msg}
    )

@app.get("/", tags=["Root"])
def root_endpoint():
    """
    General service entrypoint and health status.
    """
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "ci_cd": "GitHub Actions Active",
        "documentation": "/docs",
        "server_time": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", tags=["Health"])
def health_check():
    """
    Dedicated health check endpoint for monitoring & automated deployments.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "ci_cd": "active",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

