"""
Serializers for Jobs app.
"""
from rest_framework import serializers
from .models import Job, JobApplication
from apps.workers.models import WorkerProfile
from apps.media.serializers import MediaObjectSerializer


class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model."""
    service_name = serializers.CharField(source='service.name', read_only=True)
    poster_name = serializers.SerializerMethodField()
    photos = MediaObjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'service', 'service_name',
            'status', 'location', 'latitude', 'longitude', 'budget',
            'poster', 'poster_name', 'assigned_worker', 'scheduled_date',
            'completion_date', 'instruction_audio_url', 'photos',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'poster', 'created_at', 'updated_at']
    
    def get_poster_name(self, obj):
        return obj.poster.get_full_name()


class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for JobApplication model."""
    worker_name = serializers.CharField(source='worker.user.get_full_name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'worker', 'worker_name',
            'status', 'applied_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'applied_at', 'created_at', 'updated_at']
