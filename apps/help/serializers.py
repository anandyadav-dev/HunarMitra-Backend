"""
Serializers for Help & FAQ.
"""
from rest_framework import serializers
from apps.help.models import HelpPage, FAQ


class HelpPageSerializer(serializers.ModelSerializer):
    """Serializer for HelpPage model."""
    
    class Meta:
        model = HelpPage
        fields = ['id', 'slug', 'title', 'content_html', 'lang', 'order']
        read_only_fields = ['id']


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQ model."""
    
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'lang', 'order']
        read_only_fields = ['id']
