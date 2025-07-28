# Module for Stage 1: Data Extraction
# Enhanced data extraction with comprehensive error handling and multiple extraction strategies

import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, Any, Optional, List
import re
import utils

# Add this to your extractor.py file
def extract(url):
    """
    Main extraction function - wrapper for existing functionality
    """
    # If you have extract_content function, use it
    if hasattr(sys.modules[__name__], 'extract_content'):
        return extract_content(url)
    
    # If you have extract_blog_data function, use it  
    elif hasattr(sys.modules[__name__], 'extract_blog_data'):
        return extract_blog_data(url)
        
    # Otherwise implement basic extraction here
    else:
        import requests
        from bs4 import BeautifulSoup
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'headline': soup.find('title').get_text() if soup.find('title') else '',
                'bodyText': soup.get_text(),
                'url': url,
                'description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else ''
            }
        except Exception as e:
            raise Exception(f"Failed to extract content: {e}")

# Configure logging
logger = logging.getLogger(__name__)

def extract_primary_data(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """
    Extracts headline, description, and publication dates using multiple strategies.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        url (str): Source URL

    Returns:
        Dict containing primary data fields
    """
    data = {}

    # Headline extraction with multiple strategies
    headline_selectors = [
        'h1.entry-title',  # WordPress
        'h1.post-title',   # Common blog
        'h1[class*="title"]',
        'article h1',
        '.article-title',
        '.post-header h1',
        'h1',
        'title'
    ]

    data['headline'] = utils.get_multiple_text_from_elements(soup, headline_selectors)

    if not data['headline']:
        # Fallback to page title
        title_element = soup.find('title')
        data['headline'] = title_element.get_text(strip=True) if title_element else ""

    # Clean and validate headline
    data['headline'] = utils.clean_text(data['headline'], max_length=200)

    # Description extraction with multiple strategies
    description_selectors = [
        ('meta[name="description"]', 'content'),
        ('meta[property="og:description"]', 'content'),
        ('meta[name="twitter:description"]', 'content'),
        ('.post-excerpt', 'text'),
        ('.entry-summary', 'text'),
        ('article .summary', 'text')
    ]

    # Try meta tags first
    data['description'] = utils.get_multiple_attributes_from_elements(
        soup, [(sel, attr) for sel, attr in description_selectors if attr == 'content']
    )

    # If no meta description, try content-based extraction
    if not data['description']:
        excerpt_selectors = ['.post-excerpt', '.entry-summary', 'article .summary']
        data['description'] = utils.get_multiple_text_from_elements(soup, excerpt_selectors)

    # Clean and validate description
    data['description'] = utils.clean_text(data['description'], max_length=300)

    # Date extraction with multiple strategies
    date_selectors = [
        ('meta[property="article:published_time"]', 'content'),
        ('meta[name="article:published_time"]', 'content'),
        ('meta[property="datePublished"]', 'content'),
        ('time[datetime]', 'datetime'),
        ('time[class*="published"]', 'datetime'),
        ('.published-date', 'datetime'),
        ('.post-date time', 'datetime')
    ]

    data['datePublished'] = utils.get_multiple_attributes_from_elements(soup, date_selectors)

    # Modified date
    modified_selectors = [
        ('meta[property="article:modified_time"]', 'content'),
        ('meta[name="article:modified_time"]', 'content'),
        ('meta[property="dateModified"]', 'content'),
        ('time[class*="modified"]', 'datetime'),
        ('.modified-date', 'datetime')
    ]

    data['dateModified'] = utils.get_multiple_attributes_from_elements(soup, modified_selectors)

    logger.info(f"Extracted primary data: headline={bool(data['headline'])}, description={bool(data['description'])}, datePublished={bool(data['datePublished'])}")

    return data

def extract_author_data(soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, str]]:
    """
    Extracts author information using comprehensive patterns for different blog platforms.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): Base URL for resolving relative links

    Returns:
        Dict with author data or None if not found
    """
    # Comprehensive author patterns for different platforms
    author_patterns = [
        # WordPress patterns
        ('[class*="author"] a[href*="author"]', 'href'),
        ('a[rel="author"]', 'href'),
        ('.author-name a', 'href'),
        ('.byline a', 'href'),

        # Medium and modern blog patterns
        ('[data-testid="authorName"] a', 'href'),
        ('.author-link', 'href'),
        ('a[href*="/author/"]', 'href'),
        ('a[href*="/authors/"]', 'href'),

        # Schema.org microdata
        ('[itemtype*="Person"] a', 'href'),
        ('[itemtype*="Person"] [itemprop="url"]', 'href'),

        # Fallback patterns
        ('.post-author a', 'href'),
        ('.article-author a', 'href'),
        ('header .author a', 'href')
    ]

    for selector, href_attr in author_patterns:
        author_element = soup.select_one(selector)
        if author_element:
            name = author_element.get_text(strip=True)
            url = author_element.get(href_attr, '')

            if name and url:
                # Clean and validate
                name = utils.clean_text(name, max_length=100)
                author_url = utils.safe_url_join(base_url, url)

                if name and author_url:
                    logger.info(f"Found author: {name}")
                    return {
                        "name": name,
                        "url": author_url
                    }

    # Try structured data approach
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict) and 'author' in data:
                author = data['author']
                if isinstance(author, dict) and 'name' in author:
                    return {
                        "name": utils.clean_text(author['name'], max_length=100),
                        "url": author.get('url', '')
                    }
        except (json.JSONDecodeError, AttributeError):
            continue

    logger.warning("No author information found")
    return None

def extract_publisher_data(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """
    Extracts publisher information including name and logo.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): Base URL for resolving relative links

    Returns:
        Dict with publisher information
    """
    publisher_data = {"url": base_url}

    # Publisher name extraction
    name_selectors = [
        ('meta[property="og:site_name"]', 'content'),
        ('meta[name="application-name"]', 'content'),
        ('meta[name="site_name"]', 'content'),
        ('.site-title', 'text'),
        ('header .site-name', 'text'),
        ('.brand-name', 'text')
    ]

    publisher_name = utils.get_multiple_attributes_from_elements(
        soup, [(sel, attr) for sel, attr in name_selectors if attr == 'content']
    )

    if not publisher_name:
        # Try text-based extraction
        text_selectors = [sel for sel, attr in name_selectors if attr == 'text']
        publisher_name = utils.get_multiple_text_from_elements(soup, text_selectors)

    if not publisher_name:
        # Fallback to domain name
        try:
            from urllib.parse import urlparse
            domain = urlparse(base_url).netloc.replace('www.', '')
            publisher_name = domain.split('.')[0].title()
        except:
            publisher_name = "Unknown Publisher"

    publisher_data["name"] = utils.clean_text(publisher_name, max_length=100)

    # Logo extraction with comprehensive patterns
    logo_selectors = [
        'header img[src*="logo"]',
        'img[class*="logo"]',
        'a[class*="logo"] img',
        '.site-logo img',
        '.brand-logo img',
        'header .logo img',
        '[itemtype*="Organization"] img',
        'img[alt*="logo" i]',
        'img[alt*="brand" i]'
    ]

    logo_url = ""
    for selector in logo_selectors:
        logo_element = soup.select_one(selector)
        if logo_element:
            src = logo_element.get('src', '')
            if src:
                logo_url = utils.safe_url_join(base_url, src)
                break

    publisher_data["logo"] = {"url": logo_url}

    logger.info(f"Extracted publisher: {publisher_data['name']}, logo: {bool(logo_url)}")

    return publisher_data

def extract_featured_image(soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, str]]:
    """
    Extracts the featured image using multiple strategies.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): Base URL for resolving relative links

    Returns:
        Dict with image data or None if not found
    """
    image_selectors = [
        ('meta[property="og:image"]', 'content'),
        ('meta[name="twitter:image"]', 'content'),
        ('meta[name="thumbnail"]', 'content'),
        ('.featured-image img', 'src'),
        ('.post-thumbnail img', 'src'),
        ('article img:first-of-type', 'src'),
        ('.entry-content img:first-of-type', 'src')
    ]

    for selector, attribute in image_selectors:
        element = soup.select_one(selector)
        if element:
            image_url = element.get(attribute, '')
            if image_url:
                full_image_url = utils.safe_url_join(base_url, image_url)
                if full_image_url:
                    logger.info(f"Found featured image: {full_image_url}")
                    return {"url": full_image_url}

    logger.warning("No featured image found")
    return None

def extract_body_text(soup: BeautifulSoup) -> str:
    """
    Extracts the main article text with intelligent content detection.

    Args:
        soup (BeautifulSoup): Parsed HTML content

    Returns:
        str: Extracted body text
    """
    # Priority selectors for main content
    content_selectors = [
        'article .entry-content',  # WordPress
        'article .post-content',   # Common pattern
        '.post-body',              # Blogger
        '.entry-content',          # WordPress fallback
        '.content',                # Generic
        'main article',            # Semantic HTML
        '[role="main"] article',   # ARIA
        '.article-body',           # News sites
        '.post-text'               # Blog platforms
    ]

    content_text = ""

    for selector in content_selectors:
        content_element = soup.select_one(selector)
        if content_element:
            # Clone the element to avoid modifying the original
            content_copy = content_element.__copy__()

            # Remove unwanted elements
            unwanted_selectors = [
                'script', 'style', 'nav', 'aside', 'header', 'footer',
                '.advertisement', '.ads', '.social-share', '.related-posts',
                '.comments', '.comment-form', '.sidebar', '.widget'
            ]

            for unwanted in unwanted_selectors:
                for element in content_copy.select(unwanted):
                    element.decompose()

            content_text = content_copy.get_text(separator=' ', strip=True)
            if len(content_text) > 200:  # Minimum content threshold
                break

    # Fallback to article tag
    if not content_text or len(content_text) < 200:
        article = soup.find('article')
        if article:
            # Remove unwanted elements from article
            article_copy = article.__copy__()
            for script in article_copy(['script', 'style']):
                script.decompose()
            content_text = article_copy.get_text(separator=' ', strip=True)

    # Final fallback to body
    if not content_text or len(content_text) < 100:
        if soup.body:
            body_copy = soup.body.__copy__()
            for script in body_copy(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            content_text = body_copy.get_text(separator=' ', strip=True)

    # Clean up the extracted text
    content_text = utils.clean_text(content_text)

    logger.info(f"Extracted body text: {len(content_text)} characters")

    return content_text

def extract_additional_metadata(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """
    Extracts additional metadata that might be useful for schema generation.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): Base URL

    Returns:
        Dict with additional metadata
    """
    metadata = {}

    # Language detection
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        metadata['language'] = html_tag.get('lang')

    # Category/tags
    categories = []
    category_selectors = [
        'meta[name="keywords"]',
        '.post-categories a',
        '.entry-categories a',
        '.tags a',
        '.post-tags a'
    ]

    # Extract from meta keywords
    keywords_meta = soup.select_one('meta[name="keywords"]')
    if keywords_meta:
        keywords = keywords_meta.get('content', '')
        categories.extend([kw.strip() for kw in keywords.split(',') if kw.strip()])

    # Extract from category/tag links
    for selector in category_selectors[1:]:
        elements = soup.select(selector)
        for element in elements:
            category = element.get_text(strip=True)
            if category and category not in categories:
                categories.append(category)

    if categories:
        metadata['categories'] = categories[:10]  # Limit to 10

    # Reading time estimation
    word_count = len(extract_body_text(soup).split())
    reading_time = max(1, word_count // 200)  # Average reading speed
    metadata['estimatedReadingTime'] = f"PT{reading_time}M"  # ISO 8601 duration

    return metadata

def extract_all_data(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """
    Main orchestration function that coordinates all data extraction processes.

    Args:
        soup (BeautifulSoup): Parsed HTML content
        url (str): Source URL

    Returns:
        Dict containing all extracted data
    """
    logger.info(f"Starting data extraction for URL: {url}")

    # Initialize data structure
    base_url = utils.get_base_url(url)
    data = {"url": url}

    try:
        # Extract primary data
        primary_data = extract_primary_data(soup, url)
        data.update(primary_data)

        # Extract author information
        author_data = extract_author_data(soup, base_url)
        if author_data:
            data['author'] = author_data

        # Extract publisher information
        publisher_data = extract_publisher_data(soup, base_url)
        data['publisher'] = publisher_data

        # Extract featured image
        image_data = extract_featured_image(soup, base_url)
        if image_data:
            data['image'] = image_data

        # Extract body text
        data['bodyText'] = extract_body_text(soup)

        # Extract additional metadata
        additional_metadata = extract_additional_metadata(soup, base_url)
        data.update(additional_metadata)

        # Set up blog relationship
        data['isPartOf'] = {"url": utils.safe_url_join(base_url, "/blog/")}

        # Validate and clean the extracted data
        data = utils.validate_extracted_data(data)

        logger.info(f"Data extraction completed successfully. Fields extracted: {list(data.keys())}")

    except Exception as e:
        logger.error(f"Error during data extraction: {e}")
        # Return minimal data structure on error
        data.update({
            'headline': '',
            'description': '',
            'bodyText': '',
            'publisher': {'name': 'Unknown', 'url': base_url, 'logo': {'url': ''}}
        })

    return data
