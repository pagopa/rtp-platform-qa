def extract_id_from_location(location: str | None) -> str | None:
    """
    Extract the ID from a Location header URL.
    '.../activations/{id}' -> '{id}'.

    Returns None if location is None or empty.
    """
    if not location:
        return None
    return location.rstrip('/').split('/')[-1] or None