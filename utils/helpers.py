# utils/helpers.py

import re

def clean_text(text):
    """Remove HTML tags and trim whitespace."""
    clean = re.sub('<[^<]+?>', '', text)
    return clean.strip()

def remove_null(text):
    """Remove null or unwanted terms from text."""
    if isinstance(text, str):
        text_lower = text.lower()
        remove_terms = ['null', 'mo', 'moi']
        parts = [part.strip() for part in text.split(',')]
        parts = [part for part in parts if part and 
                part.lower() not in remove_terms and 
                len(part.strip()) > 1]  # Ensure part has meaningful content
        return ', '.join(parts)
    return text
