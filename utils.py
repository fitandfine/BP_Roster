# utils.py
"""
This module can be used for shared utility functions.
"""

def validate_date_format(date_text):
    """
    Validate if a given date_text is in the format YYYY-MM-DD.
    Returns True if valid, False otherwise.
    """
    from datetime import datetime
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False
