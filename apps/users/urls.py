"""
URL configuration for Authentication.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RequestOTPView, VerifyOTPView, LogoutView
from .views_ekyc import EKYCUploadView, EKYCStatusView

app_name = 'auth'  # Changed namespace to match URL structure better if accessed via API root

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # eKYC endpoints
    path('users/<uuid:user_id>/ekyc/upload/', EKYCUploadView.as_view(), name='ekyc-upload'),
    path('users/<uuid:user_id>/ekyc/status/', EKYCStatusView.as_view(), name='ekyc-status'),
]
