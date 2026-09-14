import os
from fastapi import FastAPI
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
    version="1.0.0",
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

@app.get("/", tags=["Root"])
def root_endpoint():
    """
    General service health check entrypoint.
    """
    return {
        "status": "online",
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "documentation": "/docs"
    }
