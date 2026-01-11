"""
Serializers for media objects.
"""
from rest_framework import serializers
from apps.media.models import MediaObject


class MediaObjectSerializer(serializers.ModelSerializer):
    """Serializer for MediaObject."""
    
    class Meta:
        model = MediaObject
        fields = ['id', 'url', 'file_type', 'file_size', 'created_at']
        read_only_fields = ['id', 'created_at']
