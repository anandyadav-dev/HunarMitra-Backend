"""
JWT Authentication middleware for Django Channels WebSocket connections.
"""
import logging
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Get user from JWT token.
    """
    try:
        from apps.users.models import User
        
        # Validate token
        UntypedToken(token_string)
        
        # Decode token to get user_id
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(token_string)
        user_id = token['user_id']
        
        # Get user
        user = User.objects.get(id=user_id)
        return user
        
    except (InvalidToken, TokenError, User.DoesNotExist) as e:
        logger.warning(f"WebSocket auth failed: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT.
    
    Token can be passed via:
    1. Query parameter: ?token=eyJ0eXAi...
    2. Subprotocol header: Sec-WebSocket-Protocol: jwt, <token>
    """
    
    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # Fallback: check subprotocols for JWT token
        if not token:
            subprotocols = scope.get('subprotocols', [])
            for i, protocol in enumerate(subprotocols):
                if protocol == 'jwt' and i + 1 < len(subprotocols):
                    # Next subprotocol should be the token
                    token = subprotocols[i + 1]
                    break
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
