from django.utils.deprecation import MiddlewareMixin
from .fake_user import FakeUser

class FakeAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        username = request.session.get('username')
        role = request.session.get('role')
        
        if username and role:
            request.user = FakeUser(username, role)
        else:
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
