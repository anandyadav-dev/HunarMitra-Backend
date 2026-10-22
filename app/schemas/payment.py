from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import UUID4, BaseModel, Field
from app.schemas.wallet import CoinLedgerResponse

class CreatePaymentOrderRequest(BaseModel):
    pack_id: Optional[UUID4] = Field(None, description="UUID of the selected coin pack")
    pack_code: Optional[str] = Field(None, description="Code of the selected coin pack (e.g. 'pack_70')")
    payment_method: Optional[str] = Field("UPI", description="Payment method / channel (e.g. 'UPI', 'CARD', 'NETBANKING')")

class PaymentOrderResponse(BaseModel):
    id: UUID4
    order_id: str
    user_id: UUID4
    pack_id: Optional[UUID4] = None
    pack_name: str
    pack_code: str
    coins: int
    bonus_coins: int
    total_coins: int
    amount_inr: Decimal
    currency: str
    status: str
    coins_credited: bool
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    credited_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    checkout_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class VerifyPaymentRequest(BaseModel):
    gateway_payment_id: str = Field(..., description="Payment ID received from gateway")
    gateway_order_id: Optional[str] = Field(None, description="Gateway order ID if returned")
    gateway_signature: str = Field(..., description="Cryptographic signature from payment gateway")

class VerifyPaymentResponse(BaseModel):
    order_id: str
    status: str
    coins_credited: bool
    coins_added: int
    wallet_balance_coins: int
    message: str

    class Config:
        from_attributes = True

class PaginatedTransactionsResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[CoinLedgerResponse]

    class Config:
        from_attributes = True

class PaginatedOrdersResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[PaymentOrderResponse]

    class Config:
        from_attributes = True
