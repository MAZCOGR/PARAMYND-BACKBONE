class ProxyFixMiddleware:
    """
    Middleware to fix HTTP_X_FORWARDED_PROTO and HTTP_X_FORWARDED_HOST
    when the app is behind multiple reverse proxies (e.g. Firebase -> Cloud Run
    or Cloudflare -> Cloud Run) resulting in "https, https" which breaks Django's is_secure().
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
        if proto:
            request.META['HTTP_X_FORWARDED_PROTO'] = proto.split(',')[0].strip()
            
        host = request.META.get('HTTP_X_FORWARDED_HOST', '')
        if host:
            request.META['HTTP_X_FORWARDED_HOST'] = host.split(',')[0].strip()
            
        return self.get_response(request)
