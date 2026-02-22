"""
Security headers middleware.

Adds Content-Security-Policy, Permissions-Policy, and other security headers
that Django does not set by default.
"""


class SecurityHeadersMiddleware:
    """Adds security headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy — defence-in-depth against XSS
        # Allows inline styles (needed by many Django template patterns) but blocks
        # inline scripts and all other unsafe sources.
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "img-src 'self' data:; "
                "frame-ancestors 'none';"
            )

        # Permissions-Policy — restrict powerful browser features
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
            )

        return response
