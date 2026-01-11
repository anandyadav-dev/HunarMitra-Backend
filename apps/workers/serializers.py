"""
Workers app serializers.
"""

from rest_framework import serializers
from .models import WorkerProfile
from apps.media.serializers import MediaObjectSerializer


class WorkerProfileSerializer(serializers.ModelSerializer):
    """Serializer for worker profiles with pricing information."""
    
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_name = serializers.SerializerMethodField()
    services_list = serializers.StringRelatedField(source='services', many=True, read_only=True)
    skills = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of skill names (mapped to Services)"
    )
    gallery = MediaObjectSerializer(many=True, read_only=True)
    distance_km = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = WorkerProfile
        fields = [
            'id',
            'user',  # Required for creation
            'user_phone',
            'user_name',
            'latitude',
            'longitude',
            'availability_status',
            'rating',
            'total_jobs_completed',
            'services_list',
            'skills',
            'price_amount',
            'price_currency',
            'price_type',
            'min_charge',
            'bio',
            'experience_years',
            'intro_audio_url',
            'gallery',
            'distance_km',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating', 'total_jobs_completed', 'services_list', 'user']
    
    def get_user_name(self, obj):
        """Get worker's full name."""
        return obj.user.get_full_name()

    def create(self, validated_data):
        skills = validated_data.pop('skills', [])
        profile = super().create(validated_data)
        self._assign_skills(profile, skills)
        return profile

    def update(self, instance, validated_data):
        skills = validated_data.pop('skills', None)
        profile = super().update(instance, validated_data)
        if skills is not None:
             # Clear existing and re-assign? Or add? usually re-assign for profile update
            instance.services.clear()
            self._assign_skills(profile, skills)
        return profile

    def _assign_skills(self, profile, skills):
        from apps.services.models import Service
        for skill_name in skills:
            # Case insensitive lookup or create
            # Assuming simplified logic for now
            service, _ = Service.objects.get_or_create(
                name__iexact=skill_name,
                defaults={
                    'name': skill_name,
                    'slug': skill_name.lower().replace(' ', '-'),
                    'is_active': True 
                }
            )
            profile.services.add(service)


class AvailabilitySerializer(serializers.Serializer):
    """Serializer for worker availability toggle."""
    
    is_available = serializers.BooleanField(
        help_text="Set worker availability status (online/offline)"
    )


class LocationUpdateSerializer(serializers.Serializer):
    """Serializer for worker location updates."""
    
    lat = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude coordinate"
    )
    lng = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude coordinate"
    )


class NearbyWorkerSerializer(serializers.ModelSerializer):
    """Serializer for nearby worker search results."""
    
    user_name = serializers.SerializerMethodField()
    service = serializers.StringRelatedField(source='services.first', read_only=True)
    distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
        help_text="Distance from search location in kilometers"
    )
    
    class Meta:
        model = WorkerProfile
        fields = [
            'id',
            'user_name',
            'service',
            'price_amount',
            'price_type',
            'rating',
            'latitude',
            'longitude',
            'distance_km',
            'is_available',
        ]
    
    def get_user_name(self, obj):
        """Get worker's full name."""
        return obj.user.get_full_name() or obj.user.phone
