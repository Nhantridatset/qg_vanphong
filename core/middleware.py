import threading

_request_local = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.user = request.user
        response = self.get_response(request)
        del _request_local.user
        return response

def get_current_user():
    return getattr(_request_local, 'user', None)
