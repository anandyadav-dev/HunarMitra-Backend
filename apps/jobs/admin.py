from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Job, JobApplication

@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ('title', 'service', 'poster', 'status', 'assigned_worker', 'created_at')
    list_filter = ('status', 'service')
    search_fields = ('title', 'description')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'service', 'poster')
        }),
        ('Location & Budget', {
            'fields': ('location', 'latitude', 'longitude', 'budget')
        }),
        ('Assignment', {
            'fields': ('status', 'assigned_worker', 'scheduled_date', 'completion_date')
        }),
        ('Audio', {
            'fields': ('instruction_audio_url',),
            'description': 'Audio instructions for the job'
        }),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(ModelAdmin):
    list_display = ('job', 'worker', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job__title', 'worker__user__phone', 'worker__user__first_name')
    readonly_fields = ('applied_at', 'created_at', 'updated_at')
