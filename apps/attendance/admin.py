from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AttendanceKiosk, AttendanceLog, Attendance


@admin.register(AttendanceKiosk)
class AttendanceKioskAdmin(ModelAdmin):
    list_display = ('location_name', 'device_uuid', 'contractor', 'is_active', 'created_at')
    list_filter = ('is_active', 'contractor')
    search_fields = ('location_name', 'device_uuid', 'address')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AttendanceLog)
class AttendanceLogAdmin(ModelAdmin):
    list_display = ('worker', 'kiosk', 'check_in', 'check_out', 'duration_hours')
    list_filter = ('kiosk', 'check_in')
    search_fields = ('worker__phone', 'kiosk__location_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'check_in'


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('worker', 'kiosk', 'date', 'method', 'device_id', 'timestamp')
    list_filter = ('method', 'date', 'kiosk')
    search_fields = ('worker__phone', 'device_id', 'kiosk__location_name')
    readonly_fields = ('timestamp', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Worker Information', {
            'fields': ('worker', 'kiosk')
        }),
        ('Attendance Details', {
            'fields': ('date', 'method', 'device_id', 'timestamp')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
