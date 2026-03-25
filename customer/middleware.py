from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

class Handle404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseNotFound):
            redirect_url = '/error/'  # Replace with your desired URL
           
            return HttpResponseRedirect(redirect_url)

        return response

class LocalhostAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is trying to access the admin path
        if request.path.startswith('/secret/'):
            # Get the visitor's IP
            remote_addr = request.META.get('REMOTE_ADDR')
            
            # If it's NOT localhost, redirect them or kill the request
            if remote_addr not in ['127.0.0.1', '::1']:
                return redirect('error') # Or HttpResponseForbidden()
                
        return self.get_response(request)