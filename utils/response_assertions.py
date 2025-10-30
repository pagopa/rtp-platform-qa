from typing import Any
from typing import Dict
from typing import Optional

from requests import Response


def is_empty_response(res: Response) -> bool:
    """
    Return True if the HTTP response body is empty or whitespace-only.
    """
    raw = res.text or ''
    return not raw.strip()
