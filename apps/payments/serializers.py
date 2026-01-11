"""
Serializers for Payments app.
"""
from rest_framework import serializers
from .models import Payment, Payout


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    booking_title = serializers.CharField(source='booking.service.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_title', 'amount', 'currency',
            'gateway', 'status', 'gateway_reference', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating payments."""
    booking_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    gateway = serializers.ChoiceField(choices=['razorpay', 'stripe', 'manual'], default='manual')


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer for Payout model."""
    worker_name = serializers.CharField(source='worker.user.get_full_name', read_only=True)
    
    class Meta:
        model = Payout
        fields = [
            'id', 'worker', 'worker_name', 'payment', 'amount',
            'currency', 'status', 'gateway_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
