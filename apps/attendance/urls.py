"""
URL configuration for Attendance app.
"""
from django.urls import path
from apps.attendance.views import KioskAttendanceView, SiteAttendanceView

urlpatterns = [
    path('attendance/kiosk/', KioskAttendanceView.as_view(), name='attendance-kiosk'),
    path('attendance/site/<uuid:kiosk_id>/', SiteAttendanceView.as_view(), name='attendance-site'),
]
