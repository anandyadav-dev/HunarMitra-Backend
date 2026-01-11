"""
Serializers for CMS app.
"""
from rest_framework import serializers
from apps.cms.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for promotional banners."""
    
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_url', 'link', 'slot', 'priority']
        read_only_fields = ['id']
