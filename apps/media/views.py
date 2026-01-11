"""
API views for media (audio upload).
"""
import uuid
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.storage import default_storage


class AudioUploadView(APIView):
    """
    Upload audio files to MinIO.
    
    Accepts mp3, wav, m4a audio files.
    Stores in MinIO under audio/uploads/
    Returns public URL.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    ALLOWED_AUDIO_TYPES = {
        'audio/mpeg',  # mp3
        'audio/mp3',
        'audio/wav',
        'audio/wave',
        'audio/x-wav',
        'audio/m4a',
        'audio/mp4',  # m4a often has this mime
    }
    
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a'}
    
    def post(self, request):
        """
        Upload audio file.
        
        Expected: multipart/form-data with 'file' field
        
        Returns:
        {
            "url": "http://minio.../audio/uploads/xyz.mp3",
            "type": "audio"
        }
        """
        audio_file = request.FILES.get('file')
        
        if not audio_file:
            return Response(
                {"error": "No file provided. Use 'file' field in multipart form."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        file_ext = os.path.splitext(audio_file.name)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    "error": f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
                    "provided": file_ext
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate content type
        content_type = audio_file.content_type
        if content_type not in self.ALLOWED_AUDIO_TYPES:
            return Response(
                {
                    "error": "Invalid audio mime type. Allowed: mp3, wav, m4a",
                    "provided": content_type
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"audio/uploads/{unique_filename}"
        
        # Save to MinIO
        try:
            saved_path = default_storage.save(file_path, audio_file)
            
            # Build public URL
            minio_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://localhost:9000')
            bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'hunarmitra')
            public_url = f"{minio_endpoint}/{bucket}/{saved_path}"
            
            return Response({
                "url": public_url,
                "type": "audio",
                "filename": unique_filename
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to upload file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageUploadView(APIView):
    """
    Upload image files to MinIO.
    
    Accepts jpg, jpeg, png, webp image files.
    Stores in MinIO under media/images/
    Returns public URL and MediaObject ID.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
    }
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    def post(self, request):
        """
        Upload image file.
        
        Expected: multipart/form-data with 'file' field
        
        Returns:
        {
            "id": "uuid",
            "url": "http://minio.../media/images/xyz.jpg",
            "file_type": "image/jpeg",
            "file_size": 12345
        }
        """
        from apps.media.models import MediaObject
        
        image_file = request.FILES.get('file')
        
        if not image_file:
            return Response(
                {"error": "No file provided. Use 'file' field in multipart form."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        file_ext = os.path.splitext(image_file.name)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    "error": f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
                    "provided": file_ext
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate content type
        content_type = image_file.content_type
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            return Response(
                {
                    "error": "Invalid image mime type. Allowed: jpg, jpeg, png, webp",
                    "provided": content_type
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"media/images/{unique_filename}"
        
        # Save to MinIO
        try:
            saved_path = default_storage.save(file_path, image_file)
            
            # Build public URL
            minio_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'http://localhost:9000')
            bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'hunarmitra')
            public_url = f"{minio_endpoint}/{bucket}/{saved_path}"
            
            # Create MediaObject
            media_obj = MediaObject.objects.create(
                key=saved_path,
                url=public_url,
                file_type=content_type,
                file_size=image_file.size,
                uploaded_by=request.user
            )
            
            return Response({
                "id": str(media_obj.id),
                "url": public_url,
                "file_type": content_type,
                "file_size": image_file.size
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to upload file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
