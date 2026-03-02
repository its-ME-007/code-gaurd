"""
Logging configuration for Cloud Key Rotation Engine
# """
# import logging
# import os
# from logging.handlers import RotatingFileHandler
# from app.core.config import settings


# def setup_logging():
#     """Configure structured logging for the application"""
    
#     # Create logs directory if it doesn't exist
#     log_dir = os.path.dirname(settings.LOG_FILE)
#     if log_dir and not os.path.exists(log_dir):
#         os.makedirs(log_dir, exist_ok=True)
    
#     logger = logging.getLogger("rotation_engine")
#     logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
#     # Console handler
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
#     # File handler with rotation
#     file_handler = RotatingFileHandler(
#         settings.LOG_FILE,
#         maxBytes=10 * 1024 * 1024,  # 10MB
#         backupCount=5
#     )
#     file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
#     # Formatter
#     formatter = logging.Formatter(
#         '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
#     console_handler.setFormatter(formatter)
#     file_handler.setFormatter(formatter)
    
#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)
    
#     return logger
