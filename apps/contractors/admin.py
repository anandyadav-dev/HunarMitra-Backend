"""
Admin interface for Contractors app.
"""
import csv
from django.contrib import admin
from django.http import HttpResponse
from unfold.admin import ModelAdmin
from .models import ContractorProfile, Site, SiteAssignment, SiteAttendance


@admin.register(ContractorProfile)
class ContractorProfileAdmin(ModelAdmin):
    """Admin for contractor profiles."""
    
    list_display = ['company_name', 'user', 'city', 'rating', 'total_projects', 'is_active']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['company_name', 'user__phone', 'user__first_name', 'license_number']
    readonly_fields = ['rating', 'total_projects', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Company Details', {
            'fields': ('company_name', 'license_number', 'gst_number', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('Statistics', {
            'fields': ('rating', 'total_projects', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Site)
class SiteAdmin(ModelAdmin):
    """Admin for construction sites."""
    
    list_display = ['name', 'contractor', 'address_short', 'is_active', 'start_date', 'created_at']
    list_filter = ['is_active', 'created_at', 'start_date']
    search_fields = ['name', 'address', 'contractor__company_name', 'contractor__user__phone']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('contractor', 'name', 'address', 'phone')
        }),
        ('Location', {
            'fields': ('lat', 'lng'),
            'description': 'Geographic coordinates for site location'
        }),
        ('Project Timeline', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def address_short(self, obj):
        """Show truncated address."""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'


@admin.register(SiteAssignment)
class SiteAssignmentAdmin(ModelAdmin):
    """Admin for worker-site assignments."""
    
    list_display = ['worker', 'site', 'role_on_site', 'assigned_at', 'is_active']
    list_filter = ['is_active', 'assigned_at', 'site']
    search_fields = ['site__name', 'worker__user__phone', 'worker__user__first_name', 'role_on_site']
    readonly_fields = ['assigned_at', 'created_at', 'updated_at']
    raw_id_fields = ['site', 'worker', 'assigned_by']
    date_hierarchy = 'assigned_at'
    
    fieldsets = (
        ('Assignment', {
            'fields': ('site', 'worker', 'role_on_site', 'is_active')
        }),
        ('Metadata', {
            'fields': ('assigned_by', 'assigned_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SiteAttendance)
class SiteAttendanceAdmin(ModelAdmin):
    """Admin for site attendance records."""
    
    list_display = ['worker', 'site', 'attendance_date', 'status', 'checkin_time', 'checkout_time']
    list_filter = ['status', 'attendance_date', 'site']
    search_fields = ['site__name', 'worker__user__phone', 'worker__user__first_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['site', 'worker', 'marked_by']
    date_hierarchy = 'attendance_date'
    
    fieldsets = (
        ('Attendance Info', {
            'fields': ('site', 'worker', 'attendance_date', 'status')
        }),
        ('Timing', {
            'fields': ('checkin_time', 'checkout_time')
        }),
        ('Additional Info', {
            'fields': ('marked_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_present', 'mark_absent', 'export_attendance_csv']
    
    def mark_present(self, request, queryset):
        """Bulk action to mark selected records as present."""
        updated = queryset.update(status=SiteAttendance.STATUS_PRESENT)
        self.message_user(request, f'{updated} attendance record(s) marked as present.')
    mark_present.short_description = 'Mark selected as Present'
    
    def mark_absent(self, request, queryset):
        """Bulk action to mark selected records as absent."""
        updated = queryset.update(status=SiteAttendance.STATUS_ABSENT)
        self.message_user(request, f'{updated} attendance record(s) marked as absent.')
    mark_absent.short_description = 'Mark selected as Absent'
    
    def export_attendance_csv(self, request, queryset):
        """Export selected attendance records to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Site', 'Worker', 'Phone', 'Date', 'Status',
            'Check-in', 'Check-out', 'Notes'
        ])
        
        for record in queryset.select_related('site', 'worker__user'):
            writer.writerow([
                record.site.name,
                record.worker.user.get_full_name() or record.worker.user.phone,
                record.worker.user.phone,
                record.attendance_date,
                record.get_status_display(),
                record.checkin_time.strftime('%H:%M') if record.checkin_time else '',
                record.checkout_time.strftime('%H:%M') if record.checkout_time else '',
                record.notes
            ])
        
        return response
    export_attendance_csv.short_description = 'Export selected to CSV'
