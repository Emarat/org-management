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
        # Allows inline styles and inline scripts (needed by Django template patterns
        # that embed <script> blocks for page-specific JS such as the sales form).
        # Ideally inline scripts would be refactored to external files and 'unsafe-inline'
        # removed from script-src, but that is a larger effort.
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://static.cloudflareinsights.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "img-src 'self' data:; "
                "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://static.cloudflareinsights.com; "
                "frame-ancestors 'none';"
            )

        # Permissions-Policy — restrict powerful browser features
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
            )

        return response
