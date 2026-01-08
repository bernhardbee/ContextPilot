"""
Logging configuration for ContextPilot backend.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (like request_id)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add any other extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "lineno", "module", "msecs", "message", 
                          "pathname", "process", "processName", "relativeCreated",
                          "thread", "threadName", "exc_info", "exc_text", "stack_info",
                          "request_id", "user_id"]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logger(name: str = "contextpilot", structured: bool = False) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        structured: If True, use structured JSON logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()

