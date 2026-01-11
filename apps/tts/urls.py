from django.urls import path
from .views import TTSStubView

urlpatterns = [
    path('', TTSStubView.as_view(), name='tts-stub'),
]
