import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

class Logger:
    """Agent-specific logger with correlation tracking"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.correlation_id = None
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(agent_id)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(f"logs/{agent_id}.log")
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    @contextmanager
    def correlation(self, correlation_id: str):
        """Context manager for correlation tracking"""
        old_id = self.correlation_id
        self.correlation_id = correlation_id
        try:
            yield
        finally:
            self.correlation_id = old_id
    
    def _format_message(self, message: str) -> str:
        if self.correlation_id:
            return f"[{self.correlation_id}] {message}"
        return message
    
    def debug(self, message: str):
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str):
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str):
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str):
        self.logger.error(self._format_message(message))
