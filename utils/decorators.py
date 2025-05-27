from django.shortcuts import redirect
from django.contrib import messages

def role_required(required_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = request.session.get('role')
            if not isinstance(required_roles, (list, tuple, set)):
                roles = (required_roles,)
            else:
                roles = required_roles
            if role not in roles:
                messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
                return redirect('show_main')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
