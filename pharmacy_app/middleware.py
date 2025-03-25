from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class RoleMiddleware(MiddlewareMixin):
    """Middleware to add user role information to the request"""
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                # Add user_role to the request for easy access in templates
                request.user_role = request.user.profile.role
            except:
                request.user_role = None
        return None
