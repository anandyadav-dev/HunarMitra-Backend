from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.schemas.wallet import WalletResponse, CoinLedgerResponse
from app.schemas.payment import PaginatedTransactionsResponse
from app.services.wallet_service import get_or_create_wallet, get_recent_transactions
from app.services.payment_service import get_paginated_transactions

router = APIRouter()

@router.get(
    "/wallet",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's wallet and coin balance",
    description="Returns current user wallet with separate purchased and earned coin balances, total coins, cash balance, and recent coin transactions."
)
def get_user_wallet(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Fetch the wallet for the authenticated user, creating one if not yet initialized.
    """
    wallet = get_or_create_wallet(db, current_user.id)
    recent_txs = get_recent_transactions(db, wallet.id, limit=10)
    
    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        balance=wallet.balance,
        purchased_coins=wallet.purchased_coins,
        earned_coins=wallet.earned_coins,
        total_coins=wallet.total_coins,
        last_updated=wallet.last_updated,
        recent_transactions=[CoinLedgerResponse.model_validate(t) for t in recent_txs]
    )

@router.get(
    "/wallet/transactions",
    response_model=PaginatedTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get paginated wallet transaction history",
    description="Returns full statement of coin credits and debits with pagination and filters (action, coin_type, transaction_type)."
)
def list_wallet_transactions(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action (CREDIT or DEBIT)"),
    coin_type: Optional[str] = Query(None, description="Filter by coin type (purchased or earned)"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type (PACK_PURCHASE, CONTACT_UNLOCK, REFUND, etc.)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get full paginated transaction ledger history for authenticated user.
    """
    return get_paginated_transactions(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        action=action,
        coin_type=coin_type,
        transaction_type=transaction_type
    )
