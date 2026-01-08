"""
Middleware for request tracking and logging.
"""
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from logger import logger


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request ID tracking and timing to all requests.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with tracking.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response with tracking headers
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Process request
        try:
            response: Response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            # Log response
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} - Error: {str(e)} ({duration_ms:.2f}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
