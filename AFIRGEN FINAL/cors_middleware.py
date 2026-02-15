"""
cors_middleware.py
-----------------------------------------------------------------------------
Enhanced CORS Middleware with Validation and Logging
-----------------------------------------------------------------------------

This module provides an enhanced CORS middleware that:
- Validates origins against a configured allowlist
- Logs rejected CORS requests for security monitoring
- Provides detailed error messages for debugging

Requirements Validated: 4.1.5 (CORS configuration validation)
"""

import logging
from typing import List, Optional
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


log = logging.getLogger(__name__)


class EnhancedCORSMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with validation and logging.
    
    This middleware wraps the standard FastAPI CORSMiddleware and adds:
    - Logging of rejected CORS requests
    - Validation of origin headers
    - Security monitoring
    
    Example usage:
        app.add_middleware(
            EnhancedCORSMiddleware,
            allow_origins=["https://example.com"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: List[str] = None,
        allow_credentials: bool = False,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        max_age: int = 600,
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or []
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET"]
        self.allow_headers = allow_headers or []
        self.max_age = max_age
        
        # Warn if wildcard is used
        if "*" in self.allow_origins:
            log.warning(
                "⚠️  CORS configured with wildcard (*) - "
                "This should only be used in development!"
            )
        
        log.info(f"Enhanced CORS middleware initialized with origins: {self.allow_origins}")
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate CORS.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler
            
        Returns:
            Response with appropriate CORS headers
        """
        origin = request.headers.get("origin")
        
        # If no origin header, not a CORS request
        if not origin:
            return await call_next(request)
        
        # Check if origin is allowed
        is_allowed = self._is_origin_allowed(origin)
        
        # Log rejected CORS requests
        if not is_allowed:
            log.warning(
                f"🚫 CORS request rejected: origin='{origin}' "
                f"from {request.client.host if request.client else 'unknown'} "
                f"to {request.method} {request.url.path}"
            )
            
            # For preflight requests, return 403
            if request.method == "OPTIONS":
                return Response(
                    content="CORS origin not allowed",
                    status_code=403,
                    headers={"Content-Type": "text/plain"}
                )
        else:
            log.debug(f"✅ CORS request allowed: origin='{origin}' to {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Add CORS headers if origin is allowed
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # For preflight requests, add additional headers
            if request.method == "OPTIONS":
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if an origin is in the allowlist.
        
        Args:
            origin: The origin to check
            
        Returns:
            True if origin is allowed, False otherwise
        """
        # Wildcard allows all origins
        if "*" in self.allow_origins:
            return True
        
        # Check exact match
        if origin in self.allow_origins:
            return True
        
        # Check with trailing slash removed
        origin_no_slash = origin.rstrip("/")
        if origin_no_slash in self.allow_origins:
            return True
        
        # Check if any allowed origin matches with trailing slash
        for allowed in self.allow_origins:
            if allowed.rstrip("/") == origin_no_slash:
                return True
        
        return False


def setup_cors_middleware(
    app,
    cors_origins: List[str],
    allow_credentials: bool = True,
    allow_methods: List[str] = None,
    allow_headers: List[str] = None,
    max_age: int = 3600,
    use_enhanced: bool = True,
) -> None:
    """
    Setup CORS middleware for the application.
    
    Args:
        app: FastAPI application
        cors_origins: List of allowed origins
        allow_credentials: Whether to allow credentials
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers
        max_age: Max age for preflight cache
        use_enhanced: Whether to use enhanced middleware with logging
    """
    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    
    if allow_headers is None:
        allow_headers = ["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"]
    
    if use_enhanced:
        app.add_middleware(
            EnhancedCORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            max_age=max_age,
        )
        log.info("✅ Enhanced CORS middleware configured")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            max_age=max_age,
        )
        log.info("✅ Standard CORS middleware configured")
