"""
TTS Stub API views.

IMPORTANT: This is a STUB implementation.
- NO real TTS processing
- Returns pre-generated audio files
- Used for frontend "Listen" buttons
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings


class TTSStubView(APIView):
    """
    Text-to-Speech stub endpoint.
    
    Returns pre-generated audio URLs based on language.
    NO runtime TTS processing.
    """
    permission_classes = [permissions.AllowAny]  # Public endpoint for Listen buttons
    
    def get(self, request):
        """
        Get TTS audio URL (stub).
        
        Query params:
        - text: (ignored in stub)
        - lang: 'en' or 'hi' (default: 'en')
        
        Returns:
        {
            "url": "http://minio.../audio/tts_stub_en.mp3",
            "lang": "en",
            "note": "This is a stub response"
        }
        """
        lang = request.query_params.get('lang', 'en').lower()
        
        # Validate language
        if lang not in ['en', 'hi']:
            return Response(
                {"error": "Invalid language. Supported: en, hi"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build MinIO URL for stub audio
        minio_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://localhost:9000')
        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'hunarmitra')
        
        # Pre-generated stub audio files
        stub_file = f"audio/tts_stub_{lang}.mp3"
        audio_url = f"{minio_endpoint}/{bucket}/{stub_file}"
        
        return Response({
            "url": audio_url,
            "lang": lang,
            "note": "This is a stub TTS response. Upload real audio files to MinIO for production."
        }, status=status.HTTP_200_OK)
