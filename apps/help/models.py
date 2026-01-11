"""
Models for Help & FAQ CMS.
"""
from django.db import models
from apps.core.models import BaseModel


class HelpPage(BaseModel):
    """Admin-editable help pages with bilingual support."""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
    ]
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier for the help page"
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the help page"
    )
    content_html = models.TextField(
        help_text="HTML content of the help page"
    )
    lang = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language of the content"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this help page is visible to users"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    class Meta:
        db_table = 'help_pages'
        verbose_name = 'Help Page'
        verbose_name_plural = 'Help Pages'
        ordering = ['order', 'title']
        indexes = [
            models.Index(fields=['lang', 'is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.lang})"


class FAQ(BaseModel):
    """Frequently Asked Questions with bilingual support."""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
    ]
    
    question = models.CharField(
        max_length=255,
        help_text="The question"
    )
    answer = models.TextField(
        help_text="The answer to the question"
    )
    lang = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language of the content"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this FAQ is visible to users"
    )
    
    class Meta:
        db_table = 'faqs'
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order', 'question']
        indexes = [
            models.Index(fields=['lang', 'is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.question[:50]}... ({self.lang})"
