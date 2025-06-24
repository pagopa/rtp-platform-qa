import random
import string


def generate_random_description(min_length: int = 0, max_length: int = 140) -> str:
    """Generate a random description string.
    
    Args:
        min_length: Minimum length of the description
        max_length: Maximum length of the description
        
    Returns:
        Random description string
    """
    length = random.randint(min_length, max_length)
    return ''.join(
        random.choices(
            string.ascii_letters + string.digits + ' ', 
            k=length
        )
    )


def generate_transaction_id() -> str:
    """Generate a transaction ID with timestamp.
    
    Returns:
        Transaction ID string in format RTP-{random}-{timestamp}
    """
    from .generators import generate_random_string
    from datetime import datetime
    
    random_part = generate_random_string(9)
    timestamp = int(datetime.now().timestamp() * 1000)
    return f"RTP-{random_part}-{timestamp}"
