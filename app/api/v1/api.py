from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, 
    customer, 
    worker, 
    contractor, 
    admin, 
    public, 
    notifications,
    wallet,
    config,
    coin_packs,
    payments,
    feedback
)

api_router = APIRouter()

# Group endpoints according to prefixes and tags for Swagger visualization
api_router.include_router(public.router, prefix="/public", tags=["Public Operations"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(wallet.router, prefix="", tags=["Wallet & Coins"])
api_router.include_router(coin_packs.router, prefix="", tags=["Coin Packs & Orders"])
api_router.include_router(payments.router, prefix="", tags=["Payments & Webhooks"])
api_router.include_router(feedback.router, prefix="", tags=["Feedback & Reviews"])
api_router.include_router(config.router, prefix="", tags=["Configuration"])
api_router.include_router(customer.router, prefix="", tags=["Customer Operations"])
api_router.include_router(worker.router, prefix="", tags=["Worker Operations"])
api_router.include_router(contractor.router, prefix="", tags=["Contractor Operations"])
api_router.include_router(admin.router, prefix="", tags=["Admin Operations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
