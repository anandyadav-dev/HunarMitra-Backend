"""
Authentication views for OTP-based login.
"""

import uuid
import logging
from django.conf import settings
from rest_framework import status, views, permissions, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User
from .serializers import (
    RequestOTPSerializer,
    RequestOTPResponseSerializer,
    VerifyOTPSerializer,
    VerifyOTPResponseSerializer,
)
from .otp_utils import (
    generate_otp,
    hash_otp,
    store_otp_in_redis,
    verify_otp,
    get_otp_from_redis,
    delete_otp_from_redis,
    check_rate_limit,
    increment_rate_limit,
)
from .tasks import send_sms

logger = logging.getLogger(__name__)


class RequestOTPView(views.APIView):
    """
    Request an OTP for phone authentication.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer

    @extend_schema(
        request=RequestOTPSerializer,
        responses={
            200: RequestOTPResponseSerializer,
            429: OpenApiResponse(description="Rate limit exceeded"),
        },
        description="Generate and send OTP to the provided phone number."
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        role = serializer.validated_data.get('role', 'worker')
        
        # 1. Check rate limits
        allowed, reason = check_rate_limit(phone)
        if not allowed:
            return Response(
                {"error": reason},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            
        # 2. Generate OTP and Request ID
        otp = generate_otp(length=4)
        hashed_otp = hash_otp(otp, phone) # Hash the OTP before storing
        request_id = str(uuid.uuid4())
        OTP_TTL_SECONDS = getattr(settings, 'OTP_EXPIRE_SECONDS', 300) # Renamed ttl to OTP_TTL_SECONDS
        
        logger.info(f"[OTP REQUEST] Phone: {phone}")
        logger.info(f"[OTP REQUEST] Generated OTP: {otp}")
        logger.info(f"[OTP REQUEST] Hashed OTP: {hashed_otp[:20]}...")
        logger.info(f"[OTP REQUEST] Request ID: {request_id}")
        
        # 3. Store in Redis
        store_otp_in_redis(request_id, phone, hashed_otp, role=role, ttl=OTP_TTL_SECONDS)
        increment_rate_limit(phone)
        
        # 4. Send SMS asynchronously
        # For dev mode, the task will log it. In prod, Twilio sends it.
        send_sms.delay(to=phone, body=f"Your HunarMitra OTP is: {otp}")
        
        # 5. Prepare Response
        response_data = {
            "request_id": request_id,
            "ttl": OTP_TTL_SECONDS,
            "message": f"OTP sent to {phone}"
        }
        
        # In DEV mode only, return OTP in response for easier testing
        if settings.DEBUG:
             response_data["dev_otp"] = otp
             
        return Response(response_data, status=status.HTTP_200_OK)


class VerifyOTPView(views.APIView):
    """
    Verify OTP and issue JWT tokens.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: VerifyOTPResponseSerializer,
            400: OpenApiResponse(description="Invalid OTP or Request ID"),
        },
        description="Verify OTP and return access/refresh tokens."
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request_id = str(serializer.validated_data['request_id'])
        otp = serializer.validated_data['otp']
        
        # 1. Retrieve OTP data
        stored_data = get_otp_from_redis(request_id)
        
        logger.info(f"[OTP VERIFY] Request ID: {request_id}")
        logger.info(f"[OTP VERIFY] Stored data found: {stored_data is not None}")
        
        if not stored_data:
            logger.error(f"[OTP VERIFY] No data found for request_id: {request_id}")
            return Response(
                {"error": "Invalid or expired request ID."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        phone = stored_data['phone']
        hashed_otp = stored_data['otp_hash']
        role = stored_data.get('role', 'worker')
        
        logger.info(f"[OTP VERIFY] Phone from cache: {phone}")
        logger.info(f"[OTP VERIFY] OTP from user: {otp}")
        logger.info(f"[OTP VERIFY] Stored hash: {hashed_otp[:20]}...")
        
        # 2. Verify OTP
        verification_result = verify_otp(otp, hashed_otp, phone)
        logger.info(f"[OTP VERIFY] Verification result: {verification_result}")
        
        if verification_result:
            # Success!
            delete_otp_from_redis(request_id)
            
            # 3. Get or Create User
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    'role': role,
                    'is_active': True,
                    'is_phone_verified': True
                }
            )
            
            if not user.is_phone_verified:
                user.is_phone_verified = True
                user.save(update_fields=['is_phone_verified'])
                
            # 4. Generate Tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "phone": str(user.phone),
                    "role": user.role,
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "is_phone_verified": user.is_phone_verified
                },
                "is_new_user": created
            }, status=status.HTTP_200_OK)
            
        else:
            # Failure
            # TODO: Increment failure counter logic in Redis if needed for strict lockout
            return Response(
                {"error": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )


class LogoutView(views.APIView):
    """
    Logout user by blacklisting the refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={205: OpenApiResponse(description="Logged out successfully")},
        description="Blacklist the refresh token to logout."
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
