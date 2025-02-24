import re
from urllib.parse import urlparse

def validate_proxy_url(url):
    """Validate proxy URL format"""
    if not url:
        return True  # Empty URL is allowed
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_input(text):
    """Sanitize user input"""
    if not text:
        return text
    # Remove any potential script tags or dangerous HTML
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<.*?>', '', text)
    return text.strip()

def format_error_message(error):
    """Format error messages for display"""
    if isinstance(error, str):
        return error
    if isinstance(error, Exception):
        return str(error)
    return "An unknown error occurred"
