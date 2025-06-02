# utils/logger.py - Centralized logging configuration

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO, log_file=None):
    """Setup centralized logging configuration"""
    
    # Create logs directory
    os.makedirs('data/logs', exist_ok=True)
    
    # Generate log filename if not provided
    if log_file is None:
        log_file = f"data/logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return root_logger
