from django.http import HttpResponse

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


class HtmxRedirectMiddleware:
    """
    Middleware to handle redirects for HTMX requests.
    If the response is a redirect and it targets one of the public / authentication
    pages, we convert it to an HTMX-triggered client-side redirect (HX-Redirect)
    to force a full browser page reload and load all proper CSS/JS.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if the request is an HTMX request
        is_htmx = request.headers.get('HX-Request') == 'true' or request.META.get('HTTP_HX_REQUEST') == 'true'
        
        # If it's an HTMX request and the response is a redirect (status codes 3xx)
        if is_htmx and 300 <= response.status_code < 400:
            redirect_url = response.url if hasattr(response, 'url') else response.get('Location')
            if redirect_url:
                # List of paths that require a full browser page reload (different templates)
                full_reload_paths = [
                    '/auth/login/',
                    '/auth/logout/',
                    '/verify-otp/',
                    '/building-workspace/',
                    '/request-demo/',
                    '/admin/',
                ]
                
                # Check if the destination URL matches any of the full reload paths
                needs_full_reload = any(path in redirect_url for path in full_reload_paths)
                
                if needs_full_reload:
                    # Convert the redirect to an HTMX-triggered client-side redirect
                    new_response = HttpResponse(status=200)
                    new_response['HX-Redirect'] = redirect_url
                    # Preserve cookies (e.g. session cookies)
                    for cookie_key, cookie_val in response.cookies.items():
                        new_response.cookies[cookie_key] = cookie_val
                    return new_response
                
        return response

