
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test, login_required


from django.http import HttpResponse
from django.urls import reverse
from django.http import Http404
def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name  # Get the name of the first group
            if group in allowed_roles:
                try:
                    return view_func(request, *args, **kwargs)
                except Http404:
                    # Handle PageNotFound error by redirecting to the school page
                    return redirect('error')
            else:
                return redirect('error')
        return wrapper_func
    return decorator

def admin_only(view_func):
    def wrapper_func(request, *args, **kwargs):
        group = 'admin'  # Set the desired group name
        user_groups = request.user.groups.all()

        for user_group in user_groups:
            if user_group.name == 'customer':
                return redirect('home')
            if user_group.name == 'admin':
                return view_func(request, *args, **kwargs)

        # If the user doesn't belong to any group or none of the groups match
        return redirect('error')

    return wrapper_func



