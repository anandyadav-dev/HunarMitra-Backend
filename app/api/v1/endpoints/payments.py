from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.services.payment_service import process_webhook_payload

router = APIRouter()

@router.post(
    "/payments/webhook",
    summary="Payment gateway signature-verified webhook",
    description="Webhook handler for payment gateways (e.g. Razorpay, Cashfree, UPI). Signature is cryptographically verified to credit coins idempotently."
)
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    x_signature: str = Header(None, alias="X-Signature"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(deps.get_db)
):
    """
    Receives asynchronous payment notifications from payment providers.
    Verifies signature and credits coins safely without duplicate transactions.
    """
    raw_body = await request.body()
    
    # Resolve signature header across providers
    signature = x_razorpay_signature or x_signature or x_hub_signature_256
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature header (X-Razorpay-Signature or X-Signature)."
        )
        
    result = process_webhook_payload(
        db=db,
        raw_payload=raw_body,
        signature_header=signature
    )
    return result
