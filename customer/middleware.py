from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect

class Handle404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseNotFound):
            redirect_url = '/error/'  # Replace with your desired URL
           
            return HttpResponseRedirect(redirect_url)

        return response
