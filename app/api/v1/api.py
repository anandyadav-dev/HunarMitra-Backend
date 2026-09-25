from fastapi import APIRouter
from app.api.v1.endpoints import auth, customer, worker, contractor, admin, public

api_router = APIRouter()

# Group endpoints according to prefixes and tags for Swagger visualization
api_router.include_router(public.router, prefix="/public", tags=["Public Operations"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(customer.router, prefix="", tags=["Customer Operations"])
api_router.include_router(worker.router, prefix="", tags=["Worker Operations"])
api_router.include_router(contractor.router, prefix="", tags=["Contractor Operations"])
api_router.include_router(admin.router, prefix="", tags=["Admin Operations"])

