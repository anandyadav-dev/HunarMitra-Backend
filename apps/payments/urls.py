from django.urls import path
from .views import PaymentCreateView, PaymentWebhookView

urlpatterns = [
    path('create/', PaymentCreateView.as_view(), name='payment-create'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
