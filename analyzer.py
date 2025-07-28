"""
Content Analysis Module
Analyzes blog content and extracts keywords, topics, and insights.
"""

import re
import logging
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Set, Optional
from collections import Counter
import pandas as pd
import numpy as np

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Advanced content analyzer with AI-powered insights."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize analyzer with optional AI capabilities."""
        self.api_key = api_key
        self.ai_enabled = False
        
        if api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.ai_enabled = True
                logger.info("AI-powered analysis enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize AI model: {str(e)}")
        
        # Common stop words for keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'amongst',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us',
            'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
    
    def analyze_content(self, content_data: Dict) -> Dict:
        """
        Perform comprehensive content analysis.
        
        Args:
            content_data (Dict): Extracted content from BlogExtractor
            
        Returns:
            Dict: Analysis results including keywords, topics, sentiment
        """
        try:
            logger.info("Starting content analysis")
            
            content = content_data.get('content', '')
            title = content_data.get('title', '')
            
            if not content:
                return self._empty_analysis("No content to analyze")
            
            # Basic analysis
            analysis = {
                'content_metrics': self._analyze_content_metrics(content),
                'keyword_analysis': self._extract_keywords(content, title),
                'readability': self._analyze_readability(content),
                'structure_analysis': self._analyze_structure(content_data),
                'seo_analysis': self._analyze_seo_factors(content_data),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
            
            # AI-powered analysis (if available)
            if self.ai_enabled:
                ai_insights = self._generate_ai_insights(content, title)
                analysis['ai_insights'] = ai_insights
            
            logger.info("Content analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during content analysis: {str(e)}")
            return self._empty_analysis(f"Analysis error: {str(e)}")
    
    def _analyze_content_metrics(self, content: str) -> Dict:
        """Analyze basic content metrics."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = content.split('\n\n')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'average_words_per_sentence': round(len(words) / max(1, len(sentences)), 2),
            'average_sentences_per_paragraph': round(len(sentences) / max(1, len(paragraphs)), 2),
            'character_count': len(content),
            'character_count_no_spaces': len(content.replace(' ', '')),
            'reading_time_minutes': max(1, round(len(words) / 200))  # 200 WPM average
        }
    
    def _extract_keywords(self, content: str, title: str = '') -> Dict:
        """Extract keywords using frequency analysis."""
        # Combine title and content with title words getting more weight
        all_text = f"{title} {title} {content}".lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)
        
        # Filter out stop words
        filtered_words = [word for word in words if word not in self.stop_words]
        
        # Count word frequencies
        word_freq = Counter(filtered_words)
        
        # Extract phrases (2-3 word combinations)
        phrases = self._extract_phrases(content.lower())
        
        # Get top keywords and phrases
        top_keywords = [
            {'word': word, 'frequency': freq, 'relevance_score': freq / len(filtered_words)}
            for word, freq in word_freq.most_common(20)
        ]
        
        top_phrases = [
            {'phrase': phrase, 'frequency': freq, 'relevance_score': freq / len(phrases)}
            for phrase, freq in Counter(phrases).most_common(10)
        ]
        
        return {
            'total_unique_words': len(set(filtered_words)),
            'keyword_density': len(filtered_words) / max(1, len(words)),
            'top_keywords': top_keywords,
            'top_phrases': top_phrases,
            'word_frequency_distribution': dict(word_freq.most_common(50))
        }
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful 2-3 word phrases."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        phrases = []
        
        # Extract 2-word phrases
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words and words[i+1] not in self.stop_words:
                phrases.append(f"{words[i]} {words[i+1]}")
        
        # Extract 3-word phrases
        for i in range(len(words) - 2):
            if (words[i] not in self.stop_words and 
                words[i+1] not in self.stop_words and 
                words[i+2] not in self.stop_words):
                phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases
    
    def _analyze_readability(self, content: str) -> Dict:
        """Analyze content readability using various metrics."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not words or not sentences:
            return {'flesch_score': 0, 'reading_level': 'Unknown'}
        
        # Calculate syllables (approximation)
        def count_syllables(word):
            word = word.lower()
            count = 0
            vowels = 'aeiouy'
            if word[0] in vowels:
                count += 1
            for index in range(1, len(word)):
                if word[index] in vowels and word[index-1] not in vowels:
                    count += 1
            if word.endswith('e'):
                count -= 1
            if count == 0:
                count += 1
            return count
        
        total_syllables = sum(count_syllables(word) for word in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        # Flesch Reading Ease Score
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))  # Clamp between 0-100
        
        # Determine reading level
        if flesch_score >= 90:
            reading_level = "Very Easy"
        elif flesch_score >= 80:
            reading_level = "Easy"
        elif flesch_score >= 70:
            reading_level = "Fairly Easy"
        elif flesch_score >= 60:
            reading_level = "Standard"
        elif flesch_score >= 50:
            reading_level = "Fairly Difficult"
        elif flesch_score >= 30:
            reading_level = "Difficult"
        else:
            reading_level = "Very Difficult"
        
        return {
            'flesch_score': round(flesch_score, 2),
            'reading_level': reading_level,
            'average_sentence_length': round(avg_sentence_length, 2),
            'average_syllables_per_word': round(avg_syllables_per_word, 2),
            'total_syllables': total_syllables
        }
    
    def _analyze_structure(self, content_data: Dict) -> Dict:
        """Analyze content structure and organization."""
        headings = content_data.get('headings', [])
        links = content_data.get('links', [])
        
        # Heading analysis
        heading_structure = {}
        for heading in headings:
            level = heading.get('level', 1)
            heading_structure[f'h{level}'] = heading_structure.get(f'h{level}', 0) + 1
        
        # Link analysis
        internal_links = [link for link in links if link.get('is_internal', False)]
        external_links = [link for link in links if not link.get('is_internal', True)]
        
        return {
            'heading_structure': heading_structure,
            'total_headings': len(headings),
            'total_links': len(links),
            'internal_links': len(internal_links),
            'external_links': len(external_links),
            'link_distribution': {
                'internal_ratio': len(internal_links) / max(1, len(links)),
                'external_ratio': len(external_links) / max(1, len(links))
            },
            'has_proper_heading_hierarchy': self._check_heading_hierarchy(headings)
        }
    
    def _check_heading_hierarchy(self, headings: List[Dict]) -> bool:
        """Check if headings follow proper hierarchical structure."""
        if not headings:
            return True
        
        prev_level = 0
        for heading in headings:
            level = heading.get('level', 1)
            if level > prev_level + 1:  # Skipped a level
                return False
            prev_level = level
        
        return True
    
    def _analyze_seo_factors(self, content_data: Dict) -> Dict:
        """Analyze SEO-related factors."""
        title = content_data.get('title', '')
        description = content_data.get('description', '')
        content = content_data.get('content', '')
        keywords = content_data.get('keywords', [])
        
        # Title analysis
        title_analysis = {
            'length': len(title),
            'word_count': len(title.split()),
            'optimal_length': 30 <= len(title) <= 60,
            'has_keywords': any(keyword.lower() in title.lower() for keyword in keywords[:5])
        }
        
        # Description analysis
        description_analysis = {
            'length': len(description),
            'word_count': len(description.split()),
            'optimal_length': 120 <= len(description) <= 160,
            'has_keywords': any(keyword.lower() in description.lower() for keyword in keywords[:5])
        }
        
        # Content analysis
        content_analysis = {
            'has_meta_description': bool(description and len(description) > 50),
            'has_headings': len(content_data.get('headings', [])) > 0,
            'has_images': bool(content_data.get('image_url')),
            'word_count_optimal': 300 <= content_data.get('word_count', 0) <= 2500
        }
        
        return {
            'title_analysis': title_analysis,
            'description_analysis': description_analysis,
            'content_analysis': content_analysis,
            'overall_seo_score': self._calculate_seo_score(title_analysis, description_analysis, content_analysis)
        }
    
    def _calculate_seo_score(self, title_analysis: Dict, description_analysis: Dict, content_analysis: Dict) -> float:
        """Calculate overall SEO score (0-100)."""
        score = 0
        total_checks = 0
        
        # Title checks
        if title_analysis['optimal_length']:
            score += 15
        if title_analysis['has_keywords']:
            score += 10
        total_checks += 25
        
        # Description checks
        if description_analysis['optimal_length']:
            score += 15
        if description_analysis['has_keywords']:
            score += 10
        total_checks += 25
        
        # Content checks
        if content_analysis['has_meta_description']:
            score += 10
        if content_analysis['has_headings']:
            score += 15
        if content_analysis['has_images']:
            score += 10
        if content_analysis['word_count_optimal']:
            score += 15
        total_checks += 50
        
        return round((score / total_checks) * 100, 2) if total_checks > 0 else 0
    
    def _generate_ai_insights(self, content: str, title: str) -> Dict:
        """Generate AI-powered content insights."""
        if not self.ai_enabled:
            return {'error': 'AI analysis not available'}
        
        try:
            # Truncate content for API limits
            truncated_content = content[:3000] + "..." if len(content) > 3000 else content
            
            prompt = f"""
            Analyze this blog post and provide insights:
            
            Title: {title}
            Content: {truncated_content}
            
            Please provide:
            1. Main topics and themes (max 5)
            2. Target audience
            3. Content sentiment (positive/neutral/negative)
            4. Suggested improvements (max 3)
            5. SEO keyword suggestions (max 10)
            
            Format as JSON.
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                ai_response = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                ai_response = {
                    'main_topics': ['Content analysis', 'Blog optimization'],
                    'target_audience': 'General audience',
                    'sentiment': 'neutral',
                    'improvements': ['Add more headings', 'Include more keywords', 'Optimize length'],
                    'keyword_suggestions': ['blog', 'content', 'analysis', 'optimization', 'SEO']
                }
            
            return ai_response
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {str(e)}")
            return {'error': f'AI analysis failed: {str(e)}'}
    
    def _empty_analysis(self, error_message: str) -> Dict:
        """Return empty analysis result with error."""
        return {
            'content_metrics': {},
            'keyword_analysis': {},
            'readability': {},
            'structure_analysis': {},
            'seo_analysis': {},
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'error': error_message
        }

def analyze_blog_content(content_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function for analyzing blog content.
    
    Args:
        content_data (Dict): Extracted content from BlogExtractor
        api_key (Optional[str]): API key for AI analysis
        
    Returns:
        Dict: Analysis results
    """
    analyzer = ContentAnalyzer(api_key)
    return analyzer.analyze_content(content_data)
