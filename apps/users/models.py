"""
Custom User model for HunarMitra.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for phone-based authentication."""
    
    def create_user(self, phone, password=None, **extra_fields):
        """Create and save a regular user."""
        if not phone:
            raise ValueError('Users must have a phone number')
        
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with phone-based authentication."""
    
    ROLE_CHOICES = [
        ('worker', 'Worker'),
        ('contractor', 'Contractor'),
        ('admin', 'Admin'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('mr', 'Marathi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='worker')
    language_preference = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    
    # Profile fields
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, null=True)
    profile_picture = models.CharField(max_length=500, blank=True, help_text="S3 key for profile picture")
    is_phone_verified = models.BooleanField(default=False)
    
    # Permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # eKYC fields (Aadhaar compliance - only last 4 digits, encrypted)
    aadhaar_last4_encrypted = models.BinaryField(
        null=True,
        blank=True,
        help_text="Encrypted last 4 digits of Aadhaar (NEVER store full Aadhaar)"
    )
    ekyc_status = models.CharField(
        max_length=16,
        choices=[
            ('none', 'None'),
            ('ocr_scanned', 'OCR Scanned'),
            ('verified', 'Verified'),
        ],
        default='none',
        help_text="eKYC verification status"
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.phone
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.phone
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.phone

    @property
    def username(self):
        """Return username (phone) for compatibility with admin templates."""
        return self.phone

    @property
    def date_joined(self):
        """Alias for created_at for compatibility with Django admin."""
        return self.created_at
    
    @property
    def aadhaar_last4_masked(self):
        """
        Return masked Aadhaar (XXXX-1234 format).
        
        Security:
            - Never returns the full number
            - Only shows last 4 digits
            - Returns None if not set
        """
        if not self.aadhaar_last4_encrypted:
            return None
        
        from core.crypto import decrypt_value
        try:
            last4 = decrypt_value(self.aadhaar_last4_encrypted)
            return f"XXXX-{last4}"
        except Exception:
            return "XXXX-****"


class OTPLog(models.Model):
    """Log of OTP requests and verification attempts."""
    
    ACTION_CHOICES = [
        ('request', 'Request'),
        ('verify_success', 'Verify Success'),
        ('verify_fail', 'Verify Fail'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, db_index=True)
    request_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'otp_logs'
        ordering = ['-created_at']
        verbose_name = 'OTP Log'
        verbose_name_plural = 'OTP Logs'
        
    def __str__(self):
        return f"{self.phone} - {self.action} - {self.created_at}"




