"""
Utility functions for core app.
"""

from django.conf import settings


def get_s3_public_url(s3_key):
    """
    Convert S3/MinIO storage key to a public URL.

    Args:
        s3_key (str): The S3 object key (e.g., 'static/logo.png')

    Returns:
        str: Full public URL to the S3 object
    """
    if not s3_key:
        return None

    endpoint = settings.AWS_S3_ENDPOINT_URL
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    # Remove leading slash if present
    s3_key = s3_key.lstrip("/")

    # Build the public URL
    return f"{endpoint}/{bucket}/{s3_key}"


# ==============================================================================
# Admin Dashboard Callbacks
# ==============================================================================

def dashboard_callback(request, context):
    """
    Customize the admin dashboard context.
    
    Args:
        request: The HTTP request object
        context: The dashboard context dict
        
    Returns:
        Modified context dict
    """
    return context


def environment_callback(request):
    """
    Return environment label for admin interface.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Environment name as string or None
    """
    from django.conf import settings
    
    if settings.DEBUG:
        return "Development"
    return "Production"
