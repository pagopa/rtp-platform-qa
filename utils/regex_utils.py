"""Regular expression utilities used across the RTP test suite.

Currently exposes patterns for validating commonly used identifiers.
"""
import re

uuidv4_pattern = re.compile(
    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'
)
