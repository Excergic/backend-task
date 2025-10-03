import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from uuid import UUID


class StructuredLogger:
    """Structured JSON logger for observability"""
    
    def __init__(self, name: str = "stories_service"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add stdout handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize special types for JSON"""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    def _log(self, level: str, event: str, **kwargs):
        """Internal log method with structured format"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            "service": "stories_service"
        }
        
        # Add all kwargs with serialization
        for key, value in kwargs.items():
            log_data[key] = self._serialize_value(value)
        
        # Log as JSON
        log_message = json.dumps(log_data)
        
        if level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "DEBUG":
            self.logger.debug(log_message)
    
    def info(self, event: str, **kwargs):
        """Log info level event"""
        self._log("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning level event"""
        self._log("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error level event"""
        self._log("ERROR", event, **kwargs)
    
    def debug(self, event: str, **kwargs):
        """Log debug level event"""
        self._log("DEBUG", event, **kwargs)
    
    # Business event helpers
    def auth_success(self, user_id: UUID, email: str):
        """Log successful authentication"""
        self.info("auth.success", user_id=user_id, email=email)
    
    def auth_failed(self, email: str, reason: str):
        """Log failed authentication"""
        self.warning("auth.failed", email=email, reason=reason)
    
    def story_created(self, story_id: UUID, author_id: UUID, visibility: str, has_media: bool):
        """Log story creation"""
        self.info(
            "story.created",
            story_id=story_id,
            author_id=author_id,
            visibility=visibility,
            has_media=has_media
        )
    
    def story_viewed(self, story_id: UUID, viewer_id: UUID, is_new_view: bool):
        """Log story view"""
        self.info(
            "story.viewed",
            story_id=story_id,
            viewer_id=viewer_id,
            is_new_view=is_new_view
        )
    
    def story_expired(self, count: int, duration_ms: float):
        """Log story expiration (from worker)"""
        self.info(
            "story.expired",
            count=count,
            duration_ms=duration_ms
        )
    
    def reaction_added(self, story_id: UUID, user_id: UUID, emoji: str):
        """Log reaction"""
        self.info(
            "reaction.added",
            story_id=story_id,
            user_id=user_id,
            emoji=emoji
        )


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        # The message is already JSON formatted
        return record.getMessage()


# Global logger instance
structured_logger = StructuredLogger()
