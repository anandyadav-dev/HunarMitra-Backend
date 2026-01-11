from django.urls import path
from .views import TrackingView

urlpatterns = [
    path('<uuid:booking_id>/', TrackingView.as_view(), name='tracking-update'),
]
