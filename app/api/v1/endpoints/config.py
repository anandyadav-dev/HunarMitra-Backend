from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.config import CoinsConfigResponse
from app.services.config_service import get_coins_config

router = APIRouter()

@router.get(
    "/config/coins",
    response_model=CoinsConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coin economy configuration and coin packs",
    description="Returns public configuration for the coin system, contact unlock costs, bonus rewards, and purchasable coin packages."
)
def get_coins_configuration(
    db: Session = Depends(deps.get_db)
):
    """
    Fetch all active coin limits, costs, packs, and promotional reward rules.
    """
    return get_coins_config(db)
