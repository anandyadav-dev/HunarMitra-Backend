"""
API views for eKYC (stub implementation).

SECURITY NOTICE:
- This is a STUB implementation for development/testing
- NO real UIDAI integration
- NO OCR processing
- Only stores LAST 4 DIGITS of Aadhaar, encrypted
- Never logs or returns full Aadhaar number
"""
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from apps.users.models import User
from core.crypto import encrypt_value


class EKYCUploadView(APIView):
    """
    Stub eKYC upload endpoint.
    
    Accepts last 4 digits of Aadhaar (or simulates extraction).
    Encrypts and stores only the last 4 digits.
    
    Security:
        - NEVER accepts or stores full Aadhaar
        - Only accepts last 4 digits
        - Encrypts before storage
        - Never logs sensitive data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """
        Upload eKYC data (stub).
        
        Expected payload:
        {
            "aadhaar_last4": "1234"
        }
        
        Returns:
        {
            "status": "success",
            "ekyc_status": "ocr_scanned",
            "aadhaar_masked": "XXXX-1234"
        }
        """
        user = get_object_or_404(User, id=user_id)
        
        # Permission check: user can only update their own eKYC
        if request.user != user and not request.user.is_staff:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get last 4 digits from request
        aadhaar_last4 = request.data.get('aadhaar_last4', '').strip()
        
        # Validate: exactly 4 digits
        if not aadhaar_last4:
            raise ValidationError({"aadhaar_last4": "This field is required"})
        
        if not re.match(r'^\d{4}$', aadhaar_last4):
            raise ValidationError({
                "aadhaar_last4": "Must be exactly 4 digits (last 4 of Aadhaar only)"
            })
        
        # Security check: ensure we're not receiving full Aadhaar
        if len(aadhaar_last4) > 4:
            raise ValidationError({
                "error": "Security violation: Only last 4 digits allowed"
            })
        
        # Encrypt before saving
        encrypted_value = encrypt_value(aadhaar_last4)
        
        # Update user
        user.aadhaar_last4_encrypted = encrypted_value
        user.ekyc_status = 'ocr_scanned'
        user.save()
        
        # Return masked response
        return Response({
            "status": "success",
            "message": "eKYC data uploaded successfully",
            "ekyc_status": user.ekyc_status,
            "aadhaar_masked": user.aadhaar_last4_masked
        }, status=status.HTTP_200_OK)


class EKYCStatusView(APIView):
    """
    Get eKYC status for a user.
    
    Security:
        - Never returns Aadhaar digits
        - Only returns verification status
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        """
        Get eKYC status.
        
        Returns:
        {
            "ekyc_status": "verified",
            "aadhaar_masked": "XXXX-1234"  // Only if available
        }
        """
        user = get_object_or_404(User, id=user_id)
        
        # Permission check
        if request.user != user and not request.user.is_staff:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response_data = {
            "ekyc_status": user.ekyc_status
        }
        
        # Add masked Aadhaar if available
        if user.aadhaar_last4_masked:
            response_data["aadhaar_masked"] = user.aadhaar_last4_masked
        
        return Response(response_data)
