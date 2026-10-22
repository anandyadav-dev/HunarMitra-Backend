from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.coin_pack import CoinPack
from app.models.user import User
from app.schemas.coin_pack import CoinPackResponse
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    PaginatedOrdersResponse
)
from app.services.payment_service import (
    create_payment_order,
    get_order_by_id,
    verify_and_credit_payment,
    get_paginated_orders
)

router = APIRouter()

@router.get(
    "/coin-packs",
    response_model=List[CoinPackResponse],
    summary="List available active coin packs",
    description="Returns all currently active coin packs with server-determined pricing and coin counts."
)
def list_active_coin_packs(db: Session = Depends(deps.get_db)):
    """
    Fetch all active and purchasable coin packages.
    """
    packs = db.query(CoinPack).filter(
        CoinPack.is_active == True,
        CoinPack.is_deleted == False
    ).order_by(CoinPack.sort_order.asc(), CoinPack.coins.asc()).all()
    return packs

@router.post(
    "/coin-packs/orders",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new coin pack payment order",
    description="Initializes a payment order for the chosen pack. The backend resolves the official price and coin quantity from the database, never trusting client-provided prices."
)
def create_order(
    req: CreatePaymentOrderRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate an order record for purchasing coins.
    """
    order = create_payment_order(
        db=db,
        user=current_user,
        pack_id=req.pack_id,
        pack_code=req.pack_code,
        payment_method=req.payment_method or "UPI"
    )
    return order

@router.get(
    "/coin-packs/orders/{order_id}",
    response_model=PaymentOrderResponse,
    summary="Poll payment order status",
    description="Checks the current status of an order (PENDING, SUCCESS, FAILED). Accessible by the purchasing user or an administrator."
)
def poll_order_status(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Poll order status during or after payment completion.
    """
    order = get_order_by_id(db, order_id_or_uuid=order_id, current_user=current_user)
    return order

@router.post(
    "/coin-packs/orders/{order_id}/verify",
    response_model=VerifyPaymentResponse,
    summary="Verify payment signature and credit coins",
    description="Validates cryptographic signature received from the payment gateway and atomically credits purchased and bonus coins to user's wallet."
)
def verify_order_payment(
    order_id: str,
    req: VerifyPaymentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Verifies payment signature from gateway and credits coins idempotently.
    """
    order = get_order_by_id(db, order_id_or_uuid=order_id, current_user=current_user)
    
    verified_order = verify_and_credit_payment(
        db=db,
        order_id=order.order_id,
        gateway_payment_id=req.gateway_payment_id,
        gateway_signature=req.gateway_signature,
        gateway_order_id=req.gateway_order_id
    )
    
    # Reload wallet for current total
    from app.services.wallet_service import get_or_create_wallet
    wallet = get_or_create_wallet(db, current_user.id)
    
    return VerifyPaymentResponse(
        order_id=verified_order.order_id,
        status=verified_order.status,
        coins_credited=verified_order.coins_credited,
        coins_added=verified_order.total_coins,
        wallet_balance_coins=wallet.total_coins,
        message="Payment verified successfully. Coins credited to your wallet."
    )

@router.get(
    "/coin-packs/my-orders",
    response_model=PaginatedOrdersResponse,
    summary="List authenticated user's coin purchase orders",
    description="Returns paginated purchase history for the current user."
)
def list_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SUCCESS, FAILED)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List user's own past coin orders.
    """
    return get_paginated_orders(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        status_filter=status
    )
