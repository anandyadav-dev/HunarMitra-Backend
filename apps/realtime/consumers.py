"""
WebSocket consumers for realtime updates.
"""
import logging
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class BookingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for booking-specific realtime updates.
    
    Clients subscribe to: /ws/bookings/{booking_id}/
    Receives: booking_status, location_update events
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.booking_group_name = f'booking_{self.booking_id}'
        self.user = self.scope.get('user')
        
        # Reject unauthenticated connections
        if isinstance(self.user, AnonymousUser):
            logger.warning(f"Unauthenticated connection attempt to booking {self.booking_id}")
            await self.close(code=4001)
            return
        
        # Check authorization
        authorized = await self.check_authorization()
        if not authorized:
            logger.warning(
                f"Unauthorized connection attempt by user {self.user.id} to booking {self.booking_id}"
            )
            await self.close(code=4003)
            return
        
        # Join booking group
        await self.channel_layer.group_add(
            self.booking_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to booking {self.booking_id}")
        
        # Send connection confirmation
        await self.send_json({
            'type': 'connection_established',
            'booking_id': str(self.booking_id),
            'message': 'Connected to booking updates'
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'booking_group_name'):
            await self.channel_layer.group_discard(
                self.booking_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from booking {self.booking_id}")
    
    async def receive_json(self, content):
        """
        Handle messages from client (optional for ACKs or commands).
        """
        message_type = content.get('type')
        
        if message_type == 'ping':
            # Respond to ping with pong
            await self.send_json({'type': 'pong'})
        else:
            # Log unknown message types
            logger.debug(f"Received client message: {content}")
    
    async def broadcast_message(self, event):
        """
        Handler for broadcast.message events from server.
        Forwards events to WebSocket client.
        """
        await self.send_json(event['event'])
    
    @database_sync_to_async
    def check_authorization(self):
        """
        Check if user is authorized to subscribe to this booking.
        
        Authorized users:
        - Booking owner (employer)
        - Assigned worker
        - Contractor (if booking has contractor relation)
        - Admin/staff
        """
        try:
            from apps.bookings.models import Booking
            
            booking = Booking.objects.select_related('user', 'worker__user').get(
                id=self.booking_id
            )
            
            # Check if user is admin/staff
            if self.user.is_staff or self.user.is_superuser:
                return True
            
            # Check if user is booking owner
            if booking.user_id == self.user.id:
                return True
            
            # Check if user is assigned worker
            if booking.worker and booking.worker.user_id == self.user.id:
                return True
            
            # TODO: Check contractor relation if implemented
            
            return False
            
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for user-level notifications.
    
    Clients subscribe to: /ws/notifications/
    Receives: All notifications for authenticated user
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        # Reject unauthenticated connections
        if isinstance(self.user, AnonymousUser):
            logger.warning("Unauthenticated connection attempt to notifications")
            await self.close(code=4001)
            return
        
        # Create user-specific group
        self.group_name = f'user_{self.user.id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to notifications channel")
        
        # Send connection confirmation
        await self.send_json({
            'type': 'connection_established',
            'message': 'Connected to notifications'
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from notifications channel")
    
    async def receive_json(self, content):
        """Handle messages from client."""
        message_type = content.get('type')
        
        if message_type == 'ping':
            await self.send_json({'type': 'pong'})
        elif message_type == 'mark_read':
            # Handle mark notification as read
            notification_id = content.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
    
    async def broadcast_message(self, event):
        """Forward notification events to client."""
        await self.send_json(event['event'])
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read."""
        try:
            from apps.notifications.models import Notification
            
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.save(update_fields=['is_read', 'updated_at'])
            
            logger.info(f"Marked notification {notification_id} as read for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
