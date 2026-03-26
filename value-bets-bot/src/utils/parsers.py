"""
parsers.py
Low-level string/numeric parsing helpers.
"""
from __future__ import annotations

from typing import Optional


def parse_float(s: str) -> Optional[float]:
    """Parse a price string to float. Returns None if not a valid odds value (> 1.0)."""
    if not s:
        return None
    try:
        v = float(s.strip().replace(",", "."))
        return v if v > 1.0 else None
    except (ValueError, TypeError):
        return None
