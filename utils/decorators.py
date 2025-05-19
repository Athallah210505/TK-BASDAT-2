from django.shortcuts import redirect
from django.contrib import messages

def role_required(required_role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = request.session.get('role')
            if role != required_role:
                messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
                return redirect('show_main')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
