import random
from datetime import datetime, timedelta


def generate_expiry_date(min_days: int = 1, max_days: int = 365) -> str:
    """Generate a random expiry date in the future.
    
    Args:
        min_days: Minimum days from now
        max_days: Maximum days from now
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    return (datetime.now() + timedelta(days=random.randint(min_days, max_days))).strftime('%Y-%m-%d')


def generate_execution_date(min_days: int = 1, max_days: int = 15) -> str:
    """Generate a random execution date in the future.
    
    Args:
        min_days: Minimum days from now
        max_days: Maximum days from now
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    return (datetime.now() + timedelta(days=random.randint(min_days, max_days))).strftime('%Y-%m-%d')


def generate_create_time() -> str:
    """Generate current timestamp for creation time.
    
    Returns:
        Timestamp string in ISO format with microseconds
    """
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def generate_future_time(minutes: int = 1) -> str:
    """Generate a future timestamp.
    
    Args:
        minutes: Minutes to add to current time
        
    Returns:
        Timestamp string in ISO format
    """
    return (datetime.now() + timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%SZ')
