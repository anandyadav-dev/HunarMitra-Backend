"""
API Views for Payments.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.conf import settings
from decimal import Decimal
import uuid
import logging

from .models import Payment, Payout
from .serializers import PaymentSerializer, PaymentCreateSerializer, PayoutSerializer
from apps.bookings.models import Booking

logger = logging.getLogger(__name__)


class PaymentCreateView(APIView):
    """
    Create a payment record (mock checkout - no real gateway).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Check if payments are enabled
        if not settings.ENABLE_PAYMENTS:
            logger.warning(
                f"Payment creation attempted but ENABLE_PAYMENTS=false. User: {request.user.id}"
            )
            return Response(
                {
                    "detail": "Online payments are currently disabled. Please use cash payment method.",
                    "code": "payments_disabled"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = PaymentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            booking_id = serializer.validated_data['booking_id']
            amount = serializer.validated_data['amount']
            gateway = serializer.validated_data.get('gateway', 'manual')
            
            # Get booking
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Verify user is booking owner
            if booking.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "Only booking owner can create payment."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create payment
            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                gateway=gateway,
                status=Payment.STATUS_CREATED
            )
            
            # Return mock checkout response
            response_data = {
                "payment_id": str(payment.id),
                "amount": str(amount),
                "currency": "INR",
                "status": "created",
                "checkout_url": f"https://mock-gateway.com/checkout/{payment.id}",
                "message": "Mock payment created (no real gateway integration)"
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentWebhookView(APIView):
    """
    Handle payment webhook (simulated).
    Updates payment status and creates payout.
    """
    permission_classes = []  # Webhooks don't need user auth
    
    def post(self, request):
        # If payments disabled, log and no-op
        if not settings.ENABLE_PAYMENTS:
            logger.info(
                "Payment webhook received but ENABLE_PAYMENTS=false. "
                "Storing raw event but not processing."
            )
            # TODO: Store raw webhook event for audit if needed
            return Response(
                {"message": "Acknowledged (payments disabled)"},
                status=status.HTTP_200_OK
            )
        
        # Parse webhook payload
        gateway_reference = request.data.get('gateway_reference')
        new_status = request.data.get('status')  # 'pending', 'completed', 'failed'
        payment_id = request.data.get('payment_id')
        
        if not payment_id or not new_status:
            return Response(
                {"error": "payment_id and status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find payment
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Idempotency check
        if payment.status == new_status:
            return Response({"message": "Payment already in this status"}, status=status.HTTP_200_OK)
        
        # Update payment
        payment.status = new_status
        if gateway_reference:
            payment.gateway_reference = gateway_reference
        payment.save()
        
        # If payment completed, create payout for worker
        if new_status == 'completed' and payment.booking.worker:
            # Calculate payout amount (e.g., 80% to worker, 20% platform fee)
            payout_amount = payment.amount * Decimal('0.80')
            
            # Check if payout already exists
            existing_payout = Payout.objects.filter(payment=payment).first()
            if not existing_payout:
                Payout.objects.create(
                    worker=payment.booking.worker,
                    payment=payment,
                    amount=payout_amount,
                    currency=payment.currency,
                    status=Payout.STATUS_PENDING
                )
        
        return Response({
            "message": "Webhook processed",
            "payment_id": str(payment.id),
            "status": payment.status
        }, status=status.HTTP_200_OK)
