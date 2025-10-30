import random
from typing import Final


MIN_PAGE_SIZE: Final[int] = 1
MAX_PAGE_SIZE: Final[int] = 128


def random_page_size(min_value: int = MIN_PAGE_SIZE, max_value: int = MAX_PAGE_SIZE) -> int:
    """
    Return a random integer in the inclusive range [min_value, max_value].
    Defaults to [1, 128] for pagination size tests.
    """
    return random.randint(min_value, max_value)