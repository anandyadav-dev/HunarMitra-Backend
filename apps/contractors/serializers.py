"""
Serializers for Contractors app - profiles and site management.
"""
from rest_framework import serializers
from .models import ContractorProfile, Site, SiteAssignment, SiteAttendance


class ContractorProfileSerializer(serializers.ModelSerializer):
    """Serializer for contractor profiles."""
    
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractorProfile
        fields = [
            'id',
            'user',
            'user_phone',
            'user_name',
            'company_name',
            'license_number',
            'gst_number',
            'address',
            'city',
            'state',
            'postal_code',
            'website',
            'experience_years',
            'rating',
            'total_projects',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'rating', 'total_projects', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        """Get contractor's name from user."""
        return obj.user.get_full_name() or obj.user.phone


class SiteSerializer(serializers.ModelSerializer):
    """Serializer for construction sites."""
    
    contractor_name = serializers.CharField(source='contractor.company_name', read_only=True)
    assigned_workers_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Site
        fields = [
            'id',
            'contractor',
            'contractor_name',
            'name',
            'address',
            'lat',
            'lng',
            'phone',
            'is_active',
            'start_date',
            'end_date',
           'metadata',
            'assigned_workers_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SiteAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for worker-site assignments."""
    
    worker_name = serializers.CharField(source='worker.user.get_full_name', read_only=True)
    worker_phone = serializers.CharField(source='worker.user.phone', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = SiteAssignment
        fields = [
            'id',
            'site',
            'site_name',
            'worker',
            'worker_name',
            'worker_phone',
            'assigned_by',
            'assigned_by_name',
            'assigned_at',
            'role_on_site',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'assigned_at', 'created_at']


class SiteAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for site attendance records."""
    
    worker_name = serializers.CharField(source='worker.user.get_full_name', read_only=True)
    worker_phone = serializers.CharField(source='worker.user.phone', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = SiteAttendance
        fields = [
            'id',
            'site',
            'site_name',
            'worker',
            'worker_name',
            'worker_phone',
            'attendance_date',
            'status',
            'checkin_time',
            'checkout_time',
            'marked_by',
            'marked_by_name',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarkAttendanceSerializer(serializers.Serializer):
    """Serializer for marking attendance."""
    
    worker_id = serializers.UUIDField(required=True)
    status = serializers.ChoiceField(choices=SiteAttendance.STATUS_CHOICES, default='present')
    checkin_time = serializers.DateTimeField(required=False, allow_null=True)
    checkout_time = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateField(required=False, allow_null=True)


class AssignWorkerSerializer(serializers.Serializer):
    """Serializer for assigning worker to site."""
    
    worker_id = serializers.UUIDField(required=True)
    role_on_site = serializers.CharField(required=False, allow_blank=True, max_length=100)


class SiteDashboardSerializer(serializers.Serializer):
    """Serializer for site dashboard metrics."""
    
    date = serializers.DateField()
    total_assigned = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    half_day_count = serializers.IntegerField()
    on_leave_count = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    on_site_now_count = serializers.IntegerField()
    pending_jobs_count = serializers.IntegerField()
    recent_timeline = serializers.ListField(child=serializers.DictField())


class ContractorDashboardSerializer(serializers.Serializer):
    """Serializer for contractor dashboard summary metrics."""
    
    active_sites = serializers.IntegerField(
        help_text="Number of active sites"
    )
    workers_present_today = serializers.IntegerField(
        help_text="Number of workers with attendance marked today"
    )
    pending_jobs = serializers.IntegerField(
        help_text="Number of jobs with status in requested/confirmed"
    )
