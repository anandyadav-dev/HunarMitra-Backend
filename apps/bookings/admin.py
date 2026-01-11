from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = (
        'id',
        'status',
        'service',
        'user',
        'worker',
        'estimated_price',
        'preferred_time',
        'created_at'
    )
    list_filter = ('status', 'created_at', 'service')
    search_fields = ('id', 'user__phone', 'worker__user__phone')
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('status', 'service', 'estimated_price', 'preferred_time')
        }),
        ('Parties', {
            'fields': ('user', 'worker')
        }),
        ('Location', {
            'fields': ('address', 'lat', 'lng', 'notes')
        }),
        ('Tracking', {
            'fields': ('eta_minutes', 'tracking_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
