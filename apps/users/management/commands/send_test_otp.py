"""
Management command to send a test OTP.
"""

from django.core.management.base import BaseCommand
from apps.users.tasks import send_sms
from datetime import datetime

class Command(BaseCommand):
    help = 'Send a test OTP to a phone number via configured SMS provider'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Phone number (e.g., +919999999999)')
        parser.add_argument('--msg', type=str, default='Test OTP: 1234', help='Custom message body')

    def handle(self, *args, **options):
        phone = options['phone']
        msg = options['msg']
        
        self.stdout.write(f"Sending test SMS to {phone}...")
        
        # Call the Celery task (using .apply() to run synchronously for feedback, or .delay() for async)
        # We use .apply() here to see the result immediately in console for testing
        try:
            # Note: In production you'd verify proper async execution using .delay()
            result = send_sms.apply(args=[phone, msg]).get()
            
            self.stdout.write(self.style.SUCCESS(f"Task executed. Result: {result}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send SMS: {e}"))
