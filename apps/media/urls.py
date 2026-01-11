from django.urls import path
from .views import AudioUploadView, ImageUploadView

urlpatterns = [
    path('audio/', AudioUploadView.as_view(), name='audio-upload'),
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
]
