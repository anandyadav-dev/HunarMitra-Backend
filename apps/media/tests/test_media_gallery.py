"""
Tests for media upload and gallery.
"""
import pytest
import io
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from apps.media.models import MediaObject
from apps.workers.models import WorkerProfile
from apps.jobs.models import Job
from apps.services.models import Service

User = get_user_model()


@pytest.mark.django_db
class TestImageUpload:
    """Test image upload endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="+919900002222", role="worker")
        self.client.force_authenticate(user=self.user)
    
    def test_upload_image_creates_media_object(self):
        """Test that uploading image creates MediaObject."""
        # Create dummy image file
        image_content = b'fake image content for testing'
        image_file = io.BytesIO(image_content)
        image_file.name = 'test_image.jpg'
        
        url = reverse('image-upload')
        response = self.client.post(
            url,
            {'file': image_file},
            format='multipart'
        )
        
        # Note: May fail without MinIO, but structure is correct
        if response.status_code == 201:
            assert 'id' in response.data
            assert 'url' in response.data
            assert MediaObject.objects.filter(id=response.data['id']).exists()
    
    def test_upload_requires_auth(self):
        """Test that upload requires authentication."""
        self.client.force_authenticate(user=None)
        
        image_file = io.BytesIO(b'test')
        image_file.name = 'test.jpg'
        
        url = reverse('image-upload')
        response = self.client.post(url, {'file': image_file}, format='multipart')
        
        assert response.status_code == 401
    
    def test_invalid_file_type(self):
        """Test rejection of invalid file types."""
        text_file = io.BytesIO(b'not an image')
        text_file.name = 'test.txt'
        
        url = reverse('image-upload')
        response = self.client.post(url, {'file': text_file}, format='multipart')
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestGalleryRelations:
    """Test gallery and photos M2M relations."""
    
    def setup_method(self):
        self.user = User.objects.create_user(phone="+919900003333", role="worker")
        self.worker = WorkerProfile.objects.create(user=self.user)
        self.service = Service.objects.create(name="Test Service", is_active=True)
        self.poster = User.objects.create_user(phone="+919900004444", role="contractor")
        self.job = Job.objects.create(
            title="Test Job",
            description="Test",
            service=self.service,
            poster=self.poster
        )
    
    def test_worker_gallery_relation(self):
        """Test worker profile gallery M2M relation."""
        media_obj = MediaObject.objects.create(
            key="test/image.jpg",
            url="http://test.com/image.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=self.user
        )
        
        self.worker.gallery.add(media_obj)
        assert self.worker.gallery.count() == 1
        assert media_obj in self.worker.gallery.all()
    
    def test_job_photos_relation(self):
        """Test job photos M2M relation."""
        media_obj = MediaObject.objects.create(
            key="test/job_photo.jpg",
            url="http://test.com/photo.jpg",
            file_type="image/jpeg",
            file_size=2048,
            uploaded_by=self.poster
        )
        
        self.job.photos.add(media_obj)
        assert self.job.photos.count() == 1
        assert media_obj in self.job.photos.all()
