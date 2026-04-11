"""
Language Detection Service – detects English vs Swahili.
"""
from app.utils.language import detect_language  # single implementation, re-exported here

__all__ = ["detect_language"]
