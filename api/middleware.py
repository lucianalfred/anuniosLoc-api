from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class SessionAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_id = request.headers.get('Session-Id') or request.headers.get('session-id')
        
        if session_id:
            from .utils import get_user_from_session
            user = get_user_from_session(session_id)
            if user:
                request.user = user
                logger.debug(f"User authenticated: {user.username}")
            else:
                logger.debug(f"Invalid session: {session_id}")
        else:
            logger.debug("No Session-Id header found")