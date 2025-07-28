"""
Content Extraction Module
Handles web scraping and content extraction from blog posts.
"""

import logging
import sys  # ← CRITICAL FIX: Added missing sys import
import requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract(url: str) -> Dict[str, Any]:
    """
    Main extraction function - wrapper for existing functionality
    
    Args:
        url (str): The URL to extract content from
        
    Returns:
        Dict[str, Any]: Extracted blog post data
    """
    logger.info(f"Starting extraction for URL: {url}")
    
    try:
        # Auto-detect the correct extraction function
        if hasattr(sys.modules[__name__], 'extract_content'):
            logger.info("Using extract_content function")
            return extract_content(url)
        elif hasattr(sys.modules[__name__], 'extract_blog_data'):
            logger.info("Using extract_blog_data function")
            return extract_blog_data(url)
        else:
            logger.info("Using fallback extraction method")
            return _fallback_extract(url)
            
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise Exception(f"Failed to extract content from {url}: {e}")

def _fallback_extract(url: str) -> Dict[str, Any]:
    """
    Fallback extraction method using basic web scraping
    
    Args:
        url (str): The URL to extract content from
        
    Returns:
        Dict[str, Any]: Basic extracted data structure
    """
    try:
        # Validate URL
        if not utils.validate_url(url):
            raise ValueError(f"Invalid URL format: {url}")
        
        # Set up user agent for requests
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch content
        logger.info(f"Fetching content from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic metadata
        title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        
        # Extract main content (try multiple selectors)
        content_selectors = [
            'article', 
            '.content', 
            '#content', 
            '.post-content',
            '.entry-content',
            'main',
            '.main-content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no specific content area found, get body text
        if not main_content:
            main_content = soup.find('body')
        
        # Clean and extract text
        body_text = main_content.get_text(strip=True, separator=' ') if main_content else soup.get_text()
        
        # Build return data structure
        extracted_data = {
            'url': url,
            'headline': title.get_text().strip() if title else '',
            'description': meta_description.get('content', '').strip() if meta_description else '',
            'bodyText': body_text[:5000],  # Limit to prevent memory issues
            'datePublished': _extract_date(soup),
            'author': _extract_author(soup),
            'image': _extract_image(soup, url),
            'wordCount': len(body_text.split()) if body_text else 0,
            'extractionMethod': 'fallback'
        }
        
        logger.info(f"Successfully extracted {extracted_data['wordCount']} words")
        return extracted_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during extraction: {e}")
        raise Exception(f"Network error: {e}")
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise Exception(f"Content extraction failed: {e}")

def _extract_date(soup: BeautifulSoup) -> str:
    """Extract publication date from various meta tags"""
    date_selectors = [
        'meta[property="article:published_time"]',
        'meta[name="date"]',
        'meta[name="pubdate"]',
        'time[datetime]',
        '.published',
        '.date'
    ]
    
    for selector in date_selectors:
        element = soup.select_one(selector)
        if element:
            if element.get('content'):
                return element.get('content')
            elif element.get('datetime'):
                return element.get('datetime')
            elif element.get_text():
                return element.get_text().strip()
    
    return ''

def _extract_author(soup: BeautifulSoup) -> str:
    """Extract author information from various meta tags"""
    author_selectors = [
        'meta[name="author"]',
        'meta[property="article:author"]',
        '.author',
        '.byline',
        '[rel="author"]'
    ]
    
    for selector in author_selectors:
        element = soup.select_one(selector)
        if element:
            if element.get('content'):
                return element.get('content')
            elif element.get_text():
                return element.get_text().strip()
    
    return ''

def _extract_image(soup: BeautifulSoup, base_url: str) -> str:
    """Extract featured image URL"""
    image_selectors = [
        'meta[property="og:image"]',
        'meta[name="twitter:image"]',
        'meta[name="image"]',
        '.featured-image img',
        'article img',
        '.post-thumbnail img'
    ]
    
    for selector in image_selectors:
        element = soup.select_one(selector)
        if element:
            img_url = element.get('content') or element.get('src')
            if img_url:
                # Convert relative URLs to absolute
                if img_url.startswith('//'):
                    return f"https:{img_url}"
                elif img_url.startswith('/'):
                    from urllib.parse import urljoin
                    return urljoin(base_url, img_url)
                elif img_url.startswith('http'):
                    return img_url
    
    return ''

# Additional extraction functions can be added here
def extract_content(url: str) -> Dict[str, Any]:
    """
    Enhanced content extraction with additional processing
    Placeholder for more sophisticated extraction logic
    """
    return _fallback_extract(url)

def extract_blog_data(url: str) -> Dict[str, Any]:
    """
    Blog-specific data extraction
    Placeholder for blog-specific extraction logic
    """
    return _fallback_extract(url)
