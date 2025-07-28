"""
Utility Functions Module
Common utilities and helper functions for the BlogPosting Schema Generator.
"""

import re
import json
import logging
import hashlib
import validators
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, urljoin
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
                'description': 'Generate SEO-optimized Schema.org structured data for blog posts',
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
                # API keys
                if 'api_keys' in st.secrets:
                    config['api_keys'] = dict(st.secrets['api_keys'])
                    if 'gemini' in config['api_keys']:
                        config['analysis']['enable_ai_analysis'] = True
                
                # App configuration overrides
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
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Remove trailing slash
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
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        try:
            domain1 = URLValidator.extract_domain(url1)
            domain2 = URLValidator.extract_domain(url2)
            return domain1 == domain2
        except Exception:
            return False

class TextProcessor:
    """Process and clean text content."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length."""
        if not text or len(text) <= max_length:
            return text
        
        # Try to cut at word boundary
        truncated = text[:max_length - len(suffix)]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # If space is reasonably close to end
            truncated = truncated[:last_space]
        
        return truncated + suffix
    
    @staticmethod
    def extract_sentences(text: str, max_sentences: int = 3) -> List[str]:
        """Extract first N sentences from text."""
        if not text:
            return []
        
        # Split by sentence endings
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences[:max_sentences]
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())
    
    @staticmethod
    def estimate_reading_time(text: str, wpm: int = 200) -> int:
        """Estimate reading time in minutes."""
        word_count = TextProcessor.count_words(text)
        return max(1, round(word_count / wpm))

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
                validation_result['errors'].append(f"Missing or empty required field: {field}")
                validation_result['is_valid'] = False
        
        # URL validation
        if data.get('url') and not URLValidator.is_valid_url(data['url']):
            validation_result['errors'].append("Invalid URL format")
            validation_result['is_valid'] = False
        
        # Content length validation
        if data.get('content') and len(data['content']) > 100000:
            validation_result['warnings'].append("Content is very long (>100k chars)")
        
        # Word count validation
        if data.get('word_count', 0) < 100:
            validation_result['warnings'].append("Content appears to be very short (<100 words)")
        
        return validation_result
    
    @staticmethod
    def validate_schema_data(schema: Dict) -> Dict:
        """Validate Schema.org structured data."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required Schema.org fields
        required_fields = ['@context', '@type', 'headline', 'author', 'publisher']
        for field in required_fields:
            if field not in schema:
                validation_result['errors'].append(f"Missing required schema field: {field}")
                validation_result['is_valid'] = False
        
        # Type validation
        if schema.get('@type') != 'BlogPosting':
            validation_result['errors'].append("Schema type should be 'BlogPosting'")
            validation_result['is_valid'] = False
        
        # Headline length
        headline = schema.get('headline', '')
        if len(headline) > 110:
            validation_result['warnings'].append("Headline is longer than recommended (110 chars)")
        
        # Description length
        description = schema.get('description', '')
        if description and len(description) > 160:
            validation_result['warnings'].append("Description is longer than recommended (160 chars)")
        
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
            return json.dumps({'error': f'JSON formatting error: {str(e)}'}, indent=indent)
    
    @staticmethod
    def minify_json(data: Dict) -> str:
        """Create minified JSON string."""
        try:
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error minifying JSON: {str(e)}")
            return json.dumps({'error': f'JSON minification error: {str(e)}'})
    
    @staticmethod
    def validate_json(json_string: str) -> Dict:
        """Validate JSON string and return validation result."""
        try:
            data = json.loads(json_string)
            return {
                'is_valid': True,
                'data': data,
                'error': None
            }
        except json.JSONDecodeError as e:
            return {
                'is_valid': False,
                'data': None,
                'error': f"JSON parsing error: {str(e)}"
            }
    
    @staticmethod
    def escape_json_for_html(json_string: str) -> str:
        """Escape JSON string for safe HTML embedding."""
        # Escape characters that could break HTML
        json_string = json_string.replace('<', '\\u003c')
        json_string = json_string.replace('>', '\\u003e')
        json_string = json_string.replace('&', '\\u0026')
        json_string = json_string.replace("'", '\\u0027')
        json_string = json_string.replace('"', '\\"')
        return json_string

class CacheManager:
    """Manage caching for expensive operations."""
    
    @staticmethod
    def generate_cache_key(url: str, params: Dict = None) -> str:
        """Generate cache key for URL and parameters."""
        key_string = url
        if params:
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            key_string += str(sorted_params)
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def cached_extraction(url: str, cache_key: str) -> Dict:
        """Placeholder for cached content extraction."""
        # This would integrate with the actual extraction function
        return {}
    
    @staticmethod
    def clear_cache():
        """Clear Streamlit cache."""
        try:
            st.cache_data.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

class ProgressTracker:
    """Track and display progress for long-running operations."""
    
    def __init__(self, total_steps: int = 5):
        """Initialize progress tracker."""
        self.total_steps = total_steps
        self.current_step = 0
        self.progress_bar = None
        self.status_text = None
    
    def start(self, title: str = "Processing..."):
        """Start progress tracking."""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.status_text.text(title)
    
    def update(self, step_name: str):
        """Update progress."""
        self.current_step += 1
        progress = self.current_step / self.total_steps
        
        if self.progress_bar:
            self.progress_bar.progress(progress)
        
        if self.status_text:
            self.status_text.text(f"Step {self.current_step}/{self.total_steps}: {step_name}")
    
    def complete(self, message: str = "Complete!"):
        """Mark as complete."""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        
        if self.status_text:
            self.status_text.text(message)
    
    def error(self, error_message: str):
        """Mark as error."""
        if self.status_text:
            self.status_text.error(f"Error: {error_message}")

class SEOHelper:
    """SEO-related utilities and recommendations."""
    
    @staticmethod
    def analyze_title_seo(title: str) -> Dict:
        """Analyze title for SEO best practices."""
        analysis = {
            'length': len(title),
            'word_count': len(title.split()),
            'recommendations': []
        }
        
        # Length recommendations
        if len(title) < 30:
            analysis['recommendations'].append("Title is too short. Aim for 30-60 characters.")
        elif len(title) > 60:
            analysis['recommendations'].append("Title is too long. Keep under 60 characters.")
        else:
            analysis['recommendations'].append("Title length is optimal.")
        
        # Word count
        if analysis['word_count'] < 4:
            analysis['recommendations'].append("Consider adding more descriptive words to the title.")
        
        # Check for numbers (often perform well)
        if re.search(r'\d', title):
            analysis['recommendations'].append("Good use of numbers in title.")
        
        return analysis
    
    @staticmethod
    def analyze_description_seo(description: str) -> Dict:
        """Analyze meta description for SEO."""
        analysis = {
            'length': len(description),
            'word_count': len(description.split()),
            'recommendations': []
        }
        
        # Length recommendations
        if len(description) < 120:
            analysis['recommendations'].append("Description is too short. Aim for 120-160 characters.")
        elif len(description) > 160:
            analysis['recommendations'].append("Description is too long. Keep under 160 characters.")
        else:
            analysis['recommendations'].append("Description length is optimal.")
        
        return analysis
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title."""
        # Convert to lowercase
        slug = title.lower()
        
        # Replace spaces and special characters with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug

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
    
    @staticmethod
    def handle_analysis_error(error: Exception, content_length: int = 0) -> Dict:
        """Handle content analysis errors."""
        error_msg = f"Failed to analyze content ({content_length} chars): {str(error)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': type(error).__name__,
            'content_length': content_length
        }
    
    @staticmethod
    def handle_schema_error(error: Exception, data_keys: List[str] = None) -> Dict:
        """Handle schema generation errors."""
        error_msg = f"Failed to generate schema: {str(error)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': type(error).__name__,
            'available_data': data_keys or []
        }

# Convenience functions
def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary."""
    return dictionary.get(key, default) if dictionary else default

def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def format_timestamp(timestamp: Union[str, datetime] = None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    elif isinstance(timestamp, str):
        try:
            from dateutil import parser
            timestamp = parser.parse(timestamp)
        except Exception:
            return str(timestamp)
    
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

def get_file_size_mb(content: str) -> float:
    """Get file size in MB for content string."""
    return len(content.encode('utf-8')) / (1024 * 1024)
