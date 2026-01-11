"""
ASGI config for hunarmitra project.

Exposes the ASGI callable as a module-level variable named `application`.

For more information on this file, see:
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hunarmitra.settings.dev')
django_asgi_app = get_asgi_application()

# Import Channels components after Django setup
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator
    
    # Import WebSocket routing
    from apps.realtime.routing import websocket_urlpatterns
    from apps.realtime.middleware import JWTAuthMiddleware
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(
                URLRouter(websocket_urlpatterns)
            )
        ),
    })
except ImportError:
    # Fallback to HTTP only if Channels not installed
    application = django_asgi_app
