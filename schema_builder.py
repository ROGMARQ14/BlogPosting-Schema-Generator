"""
Schema Builder Module
Generates Schema.org JSON-LD structured data for blog posts.
"""

import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaBuilder:
    """Build comprehensive Schema.org structured data for blog posts."""
    
    def __init__(self):
        """Initialize the schema builder."""
        self.schema_context = "https://schema.org"
        self.schema_version = "https://schema.org/version/latest/"
    
    def build_blogposting_schema(self, content_data: Dict, analysis_data: Dict = None, 
                                site_config: Dict = None) -> Dict:
        """
        Build comprehensive BlogPosting schema.
        
        Args:
            content_data (Dict): Extracted content data
            analysis_data (Dict): Content analysis results
            site_config (Dict): Website configuration
            
        Returns:
            Dict: Complete Schema.org JSON-LD structure
        """
        try:
            logger.info("Building BlogPosting schema")
            
            # Base schema structure
            schema = {
                "@context": self.schema_context,
                "@type": "BlogPosting",
                "@id": content_data.get('url', ''),
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": content_data.get('url', '')
                }
            }
            
            # Add core content properties
            schema.update(self._add_core_properties(content_data))
            
            # Add author information
            author_schema = self._build_author_schema(content_data, site_config)
            if author_schema:
                schema["author"] = author_schema
            
            # Add publisher information
            publisher_schema = self._build_publisher_schema(site_config, content_data.get('url', ''))
            if publisher_schema:
                schema["publisher"] = publisher_schema
            
            # Add image schema
            image_schema = self._build_image_schema(content_data)
            if image_schema:
                schema["image"] = image_schema
            
            # Add article body and content
            self._add_content_properties(schema, content_data)
            
            # Add SEO and analysis-based enhancements
            if analysis_data:
                self._enhance_with_analysis(schema, analysis_data, content_data)
            
            # Add technical metadata
            self._add_technical_metadata(schema, content_data)
            
            # Add breadcrumb navigation
            breadcrumb_schema = self._build_breadcrumb_schema(content_data, site_config)
            if breadcrumb_schema:
                schema["breadcrumb"] = breadcrumb_schema
            
            # Validate and clean schema
            schema = self._validate_and_clean_schema(schema)
            
            logger.info("BlogPosting schema built successfully")
            return schema
            
        except Exception as e:
            logger.error(f"Error building schema: {str(e)}")
            return self._minimal_schema(content_data)
    
    def _add_core_properties(self, content_data: Dict) -> Dict:
        """Add core BlogPosting properties."""
        properties = {}
        
        # Required properties
        if content_data.get('title'):
            properties["headline"] = content_data['title'][:110]  # Google limit
            properties["name"] = content_data['title']
        
        if content_data.get('url'):
            properties["url"] = content_data['url']
        
        # Date properties
        if content_data.get('publish_date'):
            properties["datePublished"] = self._format_date(content_data['publish_date'])
            # Use same date for dateModified if not available
            properties["dateModified"] = self._format_date(content_data['publish_date'])
        
        # Description
        if content_data.get('description'):
            properties["description"] = content_data['description'][:160]  # SEO limit
        
        # Language (default to English if not specified)
        properties["inLanguage"] = "en-US"
        
        # Content metrics
        if content_data.get('word_count'):
            properties["wordCount"] = content_data['word_count']
        
        return properties
    
    def _build_author_schema(self, content_data: Dict, site_config: Dict = None) -> Optional[Dict]:
        """Build author schema."""
        author_name = content_data.get('author', 'Unknown Author')
        
        if author_name and author_name != 'Unknown Author':
            author_schema = {
                "@type": "Person",
                "name": author_name
            }
            
            # Add additional author info if available in site config
            if site_config and 'author' in site_config:
                author_config = site_config['author']
                if isinstance(author_config, dict):
                    if author_config.get('url'):
                        author_schema["url"] = author_config['url']
                    if author_config.get('sameAs'):
                        author_schema["sameAs"] = author_config['sameAs']
                    if author_config.get('jobTitle'):
                        author_schema["jobTitle"] = author_config['jobTitle']
                    if author_config.get('worksFor'):
                        author_schema["worksFor"] = {
                            "@type": "Organization",
                            "name": author_config['worksFor']
                        }
            
            return author_schema
        
        return None
    
    def _build_publisher_schema(self, site_config: Dict = None, url: str = '') -> Dict:
        """Build publisher schema."""
        # Extract domain from URL for fallback
        domain = urlparse(url).netloc if url else 'example.com'
        
        publisher = {
            "@type": "Organization",
            "name": domain.replace('www.', '').title() if domain else "Blog Publisher"
        }
        
        if site_config and 'publisher' in site_config:
            pub_config = site_config['publisher']
            if isinstance(pub_config, dict):
                publisher["name"] = pub_config.get('name', publisher["name"])
                
                if pub_config.get('url'):
                    publisher["url"] = pub_config['url']
                
                # Add logo
                if pub_config.get('logo'):
                    publisher["logo"] = {
                        "@type": "ImageObject",
                        "url": pub_config['logo'],
                        "width": pub_config.get('logo_width', 600),
                        "height": pub_config.get('logo_height', 60)
                    }
                
                # Add social media profiles
                if pub_config.get('sameAs'):
                    publisher["sameAs"] = pub_config['sameAs']
        
        return publisher
    
    def _build_image_schema(self, content_data: Dict) -> Optional[Dict]:
        """Build image schema for the article."""
        image_url = content_data.get('image_url')
        
        if image_url:
            image_schema = {
                "@type": "ImageObject",
                "url": image_url,
                "width": 1200,  # Default values - can be customized
                "height": 630
            }
            
            # Add image caption if available
            if content_data.get('title'):
                image_schema["caption"] = content_data['title']
            
            return image_schema
        
        return None
    
    def _add_content_properties(self, schema: Dict, content_data: Dict) -> None:
        """Add content-related properties to schema."""
        # Article body
        if content_data.get('content'):
            # Truncate very long content for schema
            content = content_data['content']
            if len(content) > 5000:
                content = content[:5000] + "..."
            schema["articleBody"] = content
        
        # Article section/category
        if content_data.get('keywords'):
            # Use first keyword as primary category
            schema["articleSection"] = content_data['keywords'][0] if content_data['keywords'] else "General"
        
        # Keywords/tags
        if content_data.get('keywords'):
            schema["keywords"] = content_data['keywords'][:10]  # Limit to 10 keywords
        
        # Reading time
        if content_data.get('reading_time'):
            schema["timeRequired"] = f"PT{content_data['reading_time']}M"  # ISO 8601 duration
    
    def _enhance_with_analysis(self, schema: Dict, analysis_data: Dict, content_data: Dict) -> None:
        """Enhance schema with analysis data."""
        try:
            # Add content metrics
            if 'content_metrics' in analysis_data:
                metrics = analysis_data['content_metrics']
                if metrics.get('word_count'):
                    schema["wordCount"] = metrics['word_count']
            
            # Add keywords from analysis
            if 'keyword_analysis' in analysis_data:
                keyword_data = analysis_data['keyword_analysis']
                if keyword_data.get('top_keywords'):
                    # Extract just the keywords
                    analyzed_keywords = [kw['word'] for kw in keyword_data['top_keywords'][:15]]
                    existing_keywords = schema.get('keywords', [])
                    # Merge and deduplicate
                    all_keywords = list(set(existing_keywords + analyzed_keywords))
                    schema["keywords"] = all_keywords[:20]  # Limit to 20
            
            # Add readability information as custom property
            if 'readability' in analysis_data:
                readability = analysis_data['readability']
                schema["about"] = {
                    "@type": "Thing",
                    "name": f"Content with {readability.get('reading_level', 'Standard')} reading level"
                }
            
            # Add AI insights if available
            if 'ai_insights' in analysis_data and isinstance(analysis_data['ai_insights'], dict):
                ai_insights = analysis_data['ai_insights']
                
                # Add main topics as additional keywords
                if ai_insights.get('main_topics'):
                    existing_keywords = schema.get('keywords', [])
                    ai_keywords = [topic.lower() for topic in ai_insights['main_topics']]
                    all_keywords = list(set(existing_keywords + ai_keywords))
                    schema["keywords"] = all_keywords[:25]
                
                # Add target audience information
                if ai_insights.get('target_audience'):
                    schema["audience"] = {
                        "@type": "Audience",
                        "audienceType": ai_insights['target_audience']
                    }
        
        except Exception as e:
            logger.warning(f"Error enhancing schema with analysis: {str(e)}")
    
    def _add_technical_metadata(self, schema: Dict, content_data: Dict) -> None:
        """Add technical metadata to schema."""
        # Content encoding
        schema["encodingFormat"] = "text/html"
        
        # Content location (if different from publisher location)
        if content_data.get('url'):
            schema["contentLocation"] = {
                "@type": "Place",
                "url": content_data['url']
            }
        
        # Accessibility features (default assumptions)
        schema["accessibilityFeature"] = [
            "readingOrder",
            "structuralNavigation"
        ]
        
        # Content rating (assume general audience)
        schema["contentRating"] = "General"
        
        # Copyright info
        current_year = datetime.now().year
        if content_data.get('url'):
            domain = urlparse(content_data['url']).netloc
            schema["copyrightHolder"] = {
                "@type": "Organization",
                "name": domain.replace('www.', '').title() if domain else "Publisher"
            }
            schema["copyrightYear"] = current_year
    
    def _build_breadcrumb_schema(self, content_data: Dict, site_config: Dict = None) -> Optional[Dict]:
        """Build breadcrumb navigation schema."""
        try:
            url = content_data.get('url', '')
            if not url:
                return None
            
            parsed_url = urlparse(url)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            
            if len(path_parts) < 2:  # Not enough path elements for meaningful breadcrumbs
                return None
            
            # Build breadcrumb list
            breadcrumb_items = []
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Home page
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": base_url
            })
            
            # Intermediate path elements
            current_path = ""
            for i, part in enumerate(path_parts[:-1], 2):  # Exclude the last part (current page)
                current_path += f"/{part}"
                breadcrumb_items.append({
                    "@type": "ListItem",
                    "position": i,
                    "name": part.replace('-', ' ').replace('_', ' ').title(),
                    "item": f"{base_url}{current_path}"
                })
            
            # Current page
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": len(breadcrumb_items) + 1,
                "name": content_data.get('title', 'Current Page'),
                "item": url
            })
            
            return {
                "@type": "BreadcrumbList",
                "itemListElement": breadcrumb_items
            }
        
        except Exception as e:
            logger.warning(f"Error building breadcrumb schema: {str(e)}")
            return None
    
    def _format_date(self, date_str: str) -> str:
        """Format date string to ISO 8601."""
        try:
            # If already in ISO format, return as is
            if 'T' in date_str and ('Z' in date_str or '+' in date_str[-6:]):
                return date_str
            
            # Try to parse and convert to ISO format
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            
            # Ensure timezone info
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            
            return parsed_date.isoformat()
        
        except Exception:
            # Fallback to current time if date parsing fails
            return datetime.now(timezone.utc).isoformat()
    
    def _validate_and_clean_schema(self, schema: Dict) -> Dict:
        """Validate and clean the schema structure."""
        # Remove empty values
        cleaned_schema = {}
        for key, value in schema.items():
            if value is not None and value != "" and value != []:
                if isinstance(value, dict):
                    cleaned_value = self._validate_and_clean_schema(value)
                    if cleaned_value:
                        cleaned_schema[key] = cleaned_value
                elif isinstance(value, list):
                    cleaned_list = [item for item in value if item is not None and item != ""]
                    if cleaned_list:
                        cleaned_schema[key] = cleaned_list
                else:
                    cleaned_schema[key] = value
        
        return cleaned_schema
    
    def _minimal_schema(self, content_data: Dict) -> Dict:
        """Generate minimal valid schema as fallback."""
        return {
            "@context": self.schema_context,
            "@type": "BlogPosting",
            "headline": content_data.get('title', 'Blog Post'),
            "url": content_data.get('url', ''),
            "datePublished": datetime.now(timezone.utc).isoformat(),
            "author": {
                "@type": "Person",
                "name": content_data.get('author', 'Unknown Author')
            },
            "publisher": {
                "@type": "Organization",
                "name": "Blog Publisher"
            }
        }
    
    def format_for_html(self, schema: Dict) -> str:
        """Format schema as HTML script tag."""
        json_ld = json.dumps(schema, indent=2, ensure_ascii=False)
        return f'<script type="application/ld+json">\n{json_ld}\n</script>'
    
    def validate_schema(self, schema: Dict) -> Dict:
        """Validate schema structure and return validation results."""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Required fields validation
        required_fields = ['@context', '@type', 'headline', 'author', 'publisher']
        for field in required_fields:
            if field not in schema:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['is_valid'] = False
        
        # Type validation
        if schema.get('@type') != 'BlogPosting':
            validation_results['errors'].append("Schema type should be 'BlogPosting'")
            validation_results['is_valid'] = False
        
        # URL validation
        if not schema.get('url') or not schema.get('url').startswith(('http://', 'https://')):
            validation_results['warnings'].append("URL should be a valid absolute URL")
        
        # Date validation
        if 'datePublished' in schema:
            try:
                datetime.fromisoformat(schema['datePublished'].replace('Z', '+00:00'))
            except ValueError:
                validation_results['errors'].append("datePublished should be in ISO 8601 format")
                validation_results['is_valid'] = False
        
        # Suggestions for optimization
        if 'image' not in schema:
            validation_results['suggestions'].append("Consider adding an image for better SEO")
        
        if 'keywords' not in schema:
            validation_results['suggestions'].append("Adding keywords can improve content discoverability")
        
        return validation_results

def build_blog_schema(content_data: Dict, analysis_data: Dict = None, 
                     site_config: Dict = None) -> Dict:
    """
    Convenience function for building blog schema.
    
    Args:
        content_data (Dict): Extracted content data
        analysis_data (Dict): Optional analysis results
        site_config (Dict): Optional site configuration
        
    Returns:
        Dict: Complete Schema.org JSON-LD structure
    """
    builder = SchemaBuilder()
    return builder.build_blogposting_schema(content_data, analysis_data, site_config)
