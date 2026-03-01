"""
Time utility functions
"""
from datetime import datetime, timedelta
from typing import Tuple


def get_key_age(created_date: datetime) -> int:
    """
    Calculate key age in days.
    
    Args:
        created_date: When the key was created
    
    Returns:
        Number of days old
    """
    now = datetime.utcnow()
    age = (now - created_date.replace(tzinfo=None)).days
    return age


def format_duration(milliseconds: int) -> str:
    """
    Format milliseconds to human-readable duration.
    
    Args:
        milliseconds: Duration in milliseconds
    
    Returns:
        Formatted string (e.g., "1.2s", "250ms")
    """
    if milliseconds >= 1000:
        seconds = milliseconds / 1000
        return f"{seconds:.2f}s"
    else:
        return f"{milliseconds}ms"


def get_rotation_window(warning_days: int = 90) -> Tuple[datetime, datetime]:
    """
    Get the rotation window - keys older than this should be rotated.
    
    Args:
        warning_days: Days before rotation is recommended
    
    Returns:
        Tuple of (warning_date, rotation_date)
    """
    now = datetime.utcnow()
    rotation_date = now - timedelta(days=warning_days)
    warning_date = now - timedelta(days=warning_days - 10)
    
    return warning_date, rotation_date
