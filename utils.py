"""
Utility Functions Module
Common utilities and helper functions for the BlogPosting Schema Generator.
"""

import re
import json
import logging
import hashlib
import validators
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Dict, List, Any, Union
from urllib.parse import urlparse
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manage application configuration and settings."""
    
    @staticmethod
    def load_config() -> Dict:
        """Load configuration from Streamlit secrets or environment."""
        config = {
            'app': {
                'name': 'BlogPosting Schema Generator',
                'version': '2.0.0',
                'description': 'Generate SEO-optimized Schema.org structured data',
                'author': 'Schema Generator Team'
            },
            'extraction': {
                'timeout': 30,
                'max_retries': 3,
                'user_agent_rotation': True,
                'max_content_length': 50000
            },
            'analysis': {
                'max_keywords': 20,
                'max_phrases': 10,
                'min_word_length': 3,
                'enable_ai_analysis': False
            },
            'schema': {
                'context': 'https://schema.org',
                'max_headline_length': 110,
                'max_description_length': 160,
                'max_keywords': 25
            }
        }
        
        # Override with Streamlit secrets if available
        try:
            if hasattr(st, 'secrets'):
                if 'api_keys' in st.secrets:
                    config['api_keys'] = dict(st.secrets['api_keys'])
                    if 'gemini' in config['api_keys']:
                        config['analysis']['enable_ai_analysis'] = True
                
                if 'app_config' in st.secrets:
                    config.update(dict(st.secrets['app_config']))
        
        except Exception as e:
            logger.warning(f"Could not load secrets: {str(e)}")
        
        return config


class URLValidator:
    """Validate and normalize URLs."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            return validators.url(url)
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL format."""
        if not url:
            return url
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if url.endswith('/') and len(url) > 1:
            url = url.rstrip('/')
        
        return url
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return ''


class TextProcessor:
    """Process and clean text content."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length."""
        if not text or len(text) <= max_length:
            return text
        
        truncated = text[:max_length - len(suffix)]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:
            truncated = truncated[:last_space]
        
        return truncated + suffix
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())


class DataValidator:
    """Validate data structures and content."""
    
    @staticmethod
    def validate_content_data(data: Dict) -> Dict:
        """Validate extracted content data structure."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        required_fields = ['url', 'title', 'content']
        for field in required_fields:
            if not data.get(field):
                validation_result['errors'].append(f"Missing field: {field}")
                validation_result['is_valid'] = False
        
        if data.get('url') and not URLValidator.is_valid_url(data['url']):
            validation_result['errors'].append("Invalid URL format")
            validation_result['is_valid'] = False
        
        return validation_result


class JSONProcessor:
    """Handle JSON processing and formatting."""
    
    @staticmethod
    def format_json(data: Dict, indent: int = 2) -> str:
        """Format dictionary as pretty JSON."""
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            logger.error(f"Error formatting JSON: {str(e)}")
            return json.dumps({'error': str(e)}, indent=indent)


class ErrorHandler:
    """Centralized error handling and logging."""
    
    @staticmethod
    def handle_extraction_error(error: Exception, url: str) -> Dict:
        """Handle content extraction errors."""
        error_msg = f"Failed to extract content from {url}: {str(error)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': type(error).__name__,
            'url': url
        }


# Content extraction functions
def fetch_url_content(url: str, timeout: int = 30) -> BeautifulSoup:
    """
    Fetch and parse content from a URL.
    
    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds
        
    Returns:
        BeautifulSoup object with parsed HTML content
        
    Raises:
        requests.RequestException: If the request fails
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        raise


def extract_text_from_soup(soup: BeautifulSoup) -> str:
    """Extract clean text content from BeautifulSoup object."""
    if not soup:
        return ""
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up the text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


# Convenience functions
def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary."""
    return dictionary.get(key, default) if dictionary else default
