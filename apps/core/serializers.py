"""
Serializers for core app.
"""

from rest_framework import serializers

from apps.core.models import Banner, Theme
from apps.core.utils import get_s3_public_url
from apps.services.models import Service


class ThemeSerializer(serializers.ModelSerializer):
    """Serializer for Theme with resolved S3 URLs."""

    logo_url = serializers.SerializerMethodField()
    fonts = serializers.SerializerMethodField()

    class Meta:
        model = Theme
        fields = [
            "name",
            "primary_color",
            "accent_color",
            "background_color",
            "logo_url",
            "fonts",
        ]

    def get_logo_url(self, obj):
        """Resolve logo S3 key to public URL."""
        return get_s3_public_url(obj.logo_s3_key)

    def get_fonts(self, obj):
        """Resolve font S3 keys to public URLs."""
        fonts = obj.fonts or []
        return [
            {"family": font.get("family"), "url": get_s3_public_url(font.get("s3_key"))}
            for font in fonts
        ]


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner with resolved S3 URLs."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image_url", "action"]

    def get_image_url(self, obj):
        """Resolve image S3 key to public URL."""
        return get_s3_public_url(obj.image_s3_key)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Service/Category with resolved S3 URLs."""

    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ["id", "slug", "name", "icon_url"]

    def get_icon_url(self, obj):
        """Resolve icon S3 key to public URL."""
        return get_s3_public_url(obj.icon_s3_key)


class AppConfigSerializer(serializers.Serializer):
    """
    Main app configuration serializer that combines all config data.
    """

    app = serializers.DictField()
    theme = ThemeSerializer()
    categories = CategorySerializer(many=True)
    banners = BannerSerializer(many=True)
    features = serializers.DictField()
    meta = serializers.DictField()
