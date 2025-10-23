"""
Error handling utilities for the browser-use agent system.
"""
import logging
import sys
from typing import Any, Dict, Optional

class SafeLogger:
    """
    A safe logger that handles Unicode encoding issues.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_safe_logging()
    
    def _setup_safe_logging(self):
        """Setup logging with Unicode safety."""
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create a safe handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _safe_message(self, message: str) -> str:
        """Convert message to ASCII-safe format."""
        try:
            return message.encode('ascii', 'replace').decode('ascii')
        except:
            return str(message)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message safely."""
        safe_msg = self._safe_message(message)
        self.logger.info(safe_msg, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message safely."""
        safe_msg = self._safe_message(message)
        self.logger.warning(safe_msg, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message safely."""
        safe_msg = self._safe_message(message)
        self.logger.error(safe_msg, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message safely."""
        safe_msg = self._safe_message(message)
        self.logger.critical(safe_msg, *args, **kwargs)

def setup_global_logging():
    """Setup global logging configuration."""
    # Disable problematic loggers
    problematic_loggers = [
        'browser_use.agent.service',
        'browser_use.browser',
        'browser_use.browser.browser_session',
        'browser_use.browser.css_selector',
        'uvicorn.error',
        'uvicorn.access',
        'uvicorn.access',
        'aiohttp',
        'google.genai',
        'tenacity',
    ]
    
    for logger_name in problematic_loggers:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        logging.getLogger(logger_name).disabled = True

def safe_json_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a safe JSON response by converting Unicode characters."""
    def convert_value(value):
        if isinstance(value, str):
            return value.encode('ascii', 'replace').decode('ascii')
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(item) for item in value]
        else:
            return value
    
    return convert_value(data)
