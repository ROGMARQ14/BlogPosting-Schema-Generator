# Module for Stage 3 & 4: Schema Assembly and Finalization

import json
from datetime import datetime
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

def format_date(date_string):
    """Attempts to parse and format a date string into YYYY-MM-DD."""
    if not date_string:
        return ""
    try:
        # Handles ISO 8601 format (e.g., 2023-10-27T10:00:00+00:00)
        return datetime.fromisoformat(date_string.replace("Z", "+00:00")).strftime('%Y-%m-%d')
    except ValueError:
        # Add other common date formats to parse here if needed
        return date_string # Fallback to original if parsing fails

def build_schema(data):
    """
    Assembles the final JSON-LD schema from the collected data
    and wraps it in a script tag.
    """
    post_url = data.get('url', '')
    base_url = data.get('publisher', {}).get('url', '')

    schema = {
        "@context": "https://schema.org/",
        "@type": "BlogPosting",
        "@id": f"{post_url}#BlogPosting",
        "mainEntityOfPage": post_url,
        "headline": data.get('headline', ''),
        "name": data.get('headline', ''),
        "description": data.get('description', ''),
        "url": post_url
    }

    # --- Add conditional properties ---

    if data.get('datePublished'):
        schema['datePublished'] = format_date(data.get('datePublished'))
    if data.get('dateModified'):
        schema['dateModified'] = format_date(data.get('dateModified'))

    # Author
    author_data = data.get('author')
    if author_data and author_data.get('name') and author_data.get('url'):
        schema['author'] = {
            "@type": "Person",
            "@id": f"{author_data.get('url')}#Person",
            "name": author_data.get('name'),
            "url": author_data.get('url')
        }
        # knowsAbout could be added here if entity linking was implemented

    # Publisher
    publisher_data = data.get('publisher')
    if publisher_data and publisher_data.get('name'):
        schema['publisher'] = {
            "@type": "Organization",
            "@id": f"{base_url}#Organization",
            "name": publisher_data.get('name'),
        }
        logo_url = publisher_data.get('logo', {}).get('url')
        if logo_url:
            schema['publisher']['logo'] = {
                "@type": "ImageObject",
                "@id": logo_url,
                "url": logo_url
            }

    # Featured Image
    image_data = data.get('image')
    if image_data and image_data.get('url'):
        schema['image'] = {
            "@type": "ImageObject",
            "@id": image_data.get('url'),
            "url": image_data.get('url')
        }

    # isPartOf
    is_part_of_data = data.get('isPartOf')
    if is_part_of_data and is_part_of_data.get('url'):
        schema['isPartOf'] = {
            "@type": "Blog",
            "@id": is_part_of_data.get('url'),
            "name": f"{publisher_data.get('name', 'Website')} Blog",
            "publisher": {
                "@type": "Organization",
                "@id": f"{base_url}#Organization",
                "name": publisher_data.get('name')
            }
        }

    # Content Analysis properties
    if data.get('wordCount'):
        schema['wordCount'] = data.get('wordCount')
    if data.get('keywords'):
        schema['keywords'] = data.get('keywords')

    # Finalize by wrapping in script tag with pretty printing
    final_script = f'<script type="application/ld+json">\n{json.dumps(schema, indent=4)}\n</script>'

    return final_script


def get_wikipedia_and_wikidata_links(topic):
    """
    Searches for Wikipedia and Wikidata links for a given topic.
    Returns a dictionary with 'wikipedia' and 'wikidata' keys.
    """
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    
    # Search for Wikipedia link
    try:
        wikipedia_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={topic}&limit=1&namespace=0&format=json"
        response = requests.get(wikipedia_url, headers=headers)
        response.raise_for_status()
        wiki_data = response.json()
        wikipedia_link = wiki_data[3][0] if wiki_data[3] else None
    except (requests.exceptions.RequestException, IndexError):
        wikipedia_link = None

    # Search for Wikidata link from Wikipedia page
    wikidata_link = None
    if wikipedia_link:
        try:
            response = requests.get(wikipedia_link, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            wikidata_element = soup.select_one('li#t-wikibase > a')
            if wikidata_element:
                wikidata_link = wikidata_element['href']
        except requests.exceptions.RequestException:
            pass
            
    return {
        'wikipedia': wikipedia_link,
        'wikidata': wikidata_link
    }
