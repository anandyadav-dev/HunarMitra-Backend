"""
Serializers for Services app.
"""

from rest_framework import serializers
from django.conf import settings
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model with icon URL resolution."""
    
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = ['id', 'slug', 'title_en', 'title_hi', 'category', 'description', 'icon_url', 'display_order']
        read_only_fields = ['id']
    
    def get_icon_url(self, obj):
        """Resolve icon_s3_key to public MinIO URL."""
        if not obj.icon_s3_key:
            return None
        
        minio_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://localhost:9000')
        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'hunarmitra')
        return f"{minio_endpoint}/{bucket}/{obj.icon_s3_key}"
