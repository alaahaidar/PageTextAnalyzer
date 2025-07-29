#!/usr/bin/env python3
"""
Web Page Non-Polish Text Extractor

This script extracts visible text content from web pages and displays only
non-Polish text in an HTML table format. It identifies the language of each
text snippet and filters out Polish content.

Usage:
    python web_scraper.py <URL>
    or
    python web_scraper.py (will prompt for URL)

Dependencies:
    - requests
    - beautifulsoup4
    - langdetect
"""

import sys
import re
import html
from urllib.parse import urlparse
from typing import List, Tuple, Optional

try:
    import requests
    from bs4 import BeautifulSoup, Comment
    from langdetect import detect, DetectorFactory, LangDetectException
    from textblob import TextBlob
    import os
    from openai import OpenAI
except ImportError as e:
    print(f"Error: Missing required library. Please install: {e.name}")
    print("Install with: pip install requests beautifulsoup4 langdetect textblob openai")
    sys.exit(1)

# Set seed for consistent language detection results
DetectorFactory.seed = 0

class WebTextExtractor:
    """Extracts and analyzes text content from web pages."""
    
    # Define all relevant HTML tags for text extraction
    TEXT_TAGS = [
        'div', 'p', 'span', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'article', 'section', 'main', 'nav', 'aside', 'footer', 'header',
        'blockquote', 'li', 'td', 'th', 'caption', 'label', 'button',
        'strong', 'em', 'b', 'i', 'mark', 'small', 'del', 'ins', 'sub',
        'sup', 'code', 'pre', 'cite', 'q', 'abbr', 'time', 'address',
        'figcaption', 'summary', 'details'
    ]
    
    # Tags to completely ignore (non-visible content)
    IGNORED_TAGS = ['script', 'style', 'meta', 'link', 'noscript', 'template']
    
    # Comprehensive Polish detection patterns
    POLISH_PATTERNS = {
        # Extensive Polish words database
        'common_words': [
            # Basic words
            'aby', 'ale', 'albo', 'jako', 'oraz', 'tylko', 'także', 'bardzo', 
            'można', 'należy', 'przez', 'gdzie', 'które', 'które', 'wszystkich',
            'zostać', 'będzie', 'został', 'została', 'zostało', 'zostały',
            'może', 'mogą', 'musi', 'musisz', 'powinien', 'powinna', 'powinno',
            'więc', 'więcej', 'podczas', 'między', 'wiele', 'każdy', 'każda',
            'jakie', 'jaki', 'jaka', 'tutaj', 'teraz', 'wtedy', 'nigdy',
            'zawsze', 'często', 'czasem', 'czasami', 'dziś', 'dzisiaj',
            # Action words frequently seen
            'poznaj', 'kup', 'kupuj', 'stworzony', 'dla', 'spersonalizuj',
            'modele', 'model', 'wybierz', 'sprawdź', 'zobacz', 'odkryj',
            'znajdź', 'dowiedz', 'się', 'więcej', 'informacji', 'produkty',
            'usługi', 'sklep', 'wsparcie', 'pomoc', 'kontakt', 'firma',
            'biznes', 'biznesu', 'rozrywka', 'aplikacje', 'gry', 'muzyka',
            'filmy', 'książki', 'portfel', 'płatności', 'bezpieczeństwo',
            # Polish tech/Apple terms
            'aparat', 'zdjęcia', 'wideo', 'nagrywanie', 'odtwarzanie',
            'wyświetlacz', 'ekran', 'bateria', 'ładowanie', 'pamięć',
            'procesor', 'kamera', 'mikrofon', 'głośnik', 'słuchawki',
            # Website/navigation terms that are clearly Polish
            'mapa', 'witryny', 'stopka', 'akcesoria', 'aplikacja', 'apka',
            'konto', 'konta', 'sklep', 'sklepu', 'portfel',
            # More Polish words from the misclassified examples
            'do', 'w', 'na', 'za', 'pod', 'nad', 'przy', 'bez', 'od', 'po',
            'ze', 'we', 'przed', 'między', 'przez', 'według', 'podczas'
        ],
        
        # Polish-specific character combinations
        'char_patterns': [
            'ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż',  # Polish diacritics
            'cz', 'sz', 'rz', 'dz', 'dż', 'dź',  # Polish digraphs
        ],
        
        # Comprehensive Polish endings
        'endings': [
            'ość', 'anie', 'enie', 'owy', 'owa', 'owe', 'emy', 'ecie',
            'ować', 'ąć', 'nąć', 'ić', 'yć', 'ych', 'ymi', 'ami', 'ach',
            'iej', 'iego', 'ych', 'ymi', 'ę', 'ą', 'em', 'ie', 'ów',
            'uj', 'esz', 'isz', 'asz', 'uje', 'uję', 'iesz'
        ],
        
        # Polish possessive and genitive patterns
        'possessive_patterns': [
            "'a", "'em", "'ie", "'y", "'ę", "'ą"  # iPhone'a, Apple'a etc
        ],
        
        # Polish phrases that are commonly misidentified
        'polish_phrases': [
            'mapa witryny',      # Was classified as Swahili 
            'akcesoria do',      # Was classified as Portuguese
            'stopka apple',      # Was classified as Slovenian
            'aplikacja apple',   # Was classified as Slovenian
            'konto w apple',     # Contains Polish preposition
            'iphone i mac',      # Polish conjunction 'i'
            'iphone i apple',    # Polish conjunction 'i'
            'iphone i airpods'   # Polish conjunction 'i'
        ]
    }
    
    def __init__(self, timeout: int = 30):
        """Initialize the extractor with request timeout."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.openai_client = None
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def fetch_page(self, url: str) -> str:
        """Fetch HTML content from URL with error handling."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to the URL")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.reason}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove text that's too short to be meaningful
        if len(text) < 3:
            return ""
        
        # Remove text that's mostly numbers or special characters
        if re.match(r'^[\d\s\W]*$', text):
            return ""
        
        return text
    
    def is_polish_text(self, text: str) -> bool:
        """Ultra-aggressive Polish text detection for maximum accuracy."""
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Strategy 1: Polish diacritics (any Polish character = Polish text)
        polish_chars = sum(1 for char in text if char in 'ąćęłńóśźż')
        if polish_chars > 0:
            return True
        
        # Strategy 2: Polish possessive patterns (iPhone'a, Apple'a etc)
        for pattern in self.POLISH_PATTERNS['possessive_patterns']:
            if pattern in text_lower:
                return True
        
        # Strategy 2.5: Polish phrases that are commonly misidentified
        for phrase in self.POLISH_PATTERNS['polish_phrases']:
            if phrase in text_lower:
                return True
        
        # Strategy 3: Exact Polish word matches (much more aggressive)
        polish_word_count = 0
        for word in words:
            # Remove punctuation and check
            clean_word = word.strip('.,!?;:"()[]{}')
            if clean_word in self.POLISH_PATTERNS['common_words']:
                polish_word_count += 1
        
        if len(words) > 0:
            polish_word_ratio = polish_word_count / len(words)
            # Much lower threshold - even 1 Polish word in short text
            if len(words) <= 3 and polish_word_count >= 1:  # Short phrases
                return True
            elif polish_word_ratio > 0.1:  # 10% threshold instead of 15%
                return True
        
        # Strategy 4: Polish character combinations (more sensitive)
        polish_patterns = sum(1 for pattern in self.POLISH_PATTERNS['char_patterns'] 
                             if pattern in text_lower)
        if polish_patterns >= 1:  # Even 1 pattern is enough
            return True
        
        # Strategy 5: Polish word endings (more aggressive)
        polish_endings = 0
        for word in words:
            clean_word = word.strip('.,!?;:"()[]{}')
            for ending in self.POLISH_PATTERNS['endings']:
                if clean_word.endswith(ending):
                    polish_endings += 1
                    break
        
        if len(words) > 0 and polish_endings / len(words) > 0.05:  # 5% threshold
            return True
        
        # Strategy 6: Single word Polish detection for very short text
        if len(words) == 1:
            clean_word = words[0].strip('.,!?;:"()[]{}')
            if (clean_word in self.POLISH_PATTERNS['common_words'] or 
                any(ending in clean_word for ending in self.POLISH_PATTERNS['endings']) or
                any(pattern in clean_word for pattern in self.POLISH_PATTERNS['char_patterns'])):
                return True
        
        # Strategy 6.5: Special Polish conjunction detection ('i' = and)
        # Phrases like "iPhone i Mac", "iPhone i Apple" are clearly Polish
        if ' i ' in text_lower and len(words) >= 3:
            # Check if it's "X i Y" pattern where X and Y are brands/products
            words_around_i = []
            for i, word in enumerate(words):
                if word == 'i' and i > 0 and i < len(words) - 1:
                    words_around_i.extend([words[i-1], words[i+1]])
            
            # If we have brand names around 'i', it's likely Polish
            brand_terms = ['iphone', 'apple', 'mac', 'airpods', 'watch', 'ipad', 'imac']
            if any(term in ' '.join(words_around_i).lower() for term in brand_terms):
                return True
        
        # Strategy 7: Use langdetect ONLY if our patterns didn't catch it
        try:
            if len(text.strip()) >= 10:
                detected_lang = detect(text)
                if detected_lang == 'pl':
                    return True
        except:
            pass
        
        return False
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of text snippet with enhanced Polish detection."""
        try:
            # Skip very short text for better accuracy
            if len(text.strip()) < 5:
                return None
            
            # First check if it's Polish using our enhanced detection
            if self.is_polish_text(text):
                return 'pl'
            
            # For non-Polish text, use langdetect
            if len(text.strip()) >= 10:
                detected_lang = detect(text)
                return detected_lang
            else:
                return None
                
        except LangDetectException:
            # If langdetect fails, return None (TextBlob doesn't have detect_language)
            return None
        except Exception:
            return None
    
    def extract_text_elements(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extract text content from all relevant HTML elements."""
        text_elements = []
        
        # Remove ignored tags completely
        for tag_name in self.IGNORED_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extract text from relevant tags
        for tag_name in self.TEXT_TAGS:
            elements = soup.find_all(tag_name)
            
            for element in elements:
                # Get the text content of the element (includes nested text)
                text_content = element.get_text(separator=' ', strip=True)
                
                # Clean the extracted text
                cleaned_text = self.clean_text(text_content)
                
                if cleaned_text:
                    text_elements.append((tag_name, cleaned_text))
        
        return text_elements
    
    def filter_non_polish(self, text_elements: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        """Filter out Polish content and return non-Polish text with detected language."""
        non_polish_elements = []
        
        for tag_name, text in text_elements:
            detected_lang = self.detect_language(text)
            
            # Skip if language detection failed or if it's Polish
            if detected_lang is None or detected_lang == 'pl':
                continue
            
            non_polish_elements.append((tag_name, detected_lang, text))
        
        return non_polish_elements
    
    def generate_html_table(self, elements: List[Tuple[str, str, str]]) -> str:
        """Generate HTML table with non-Polish content."""
        if not elements:
            return """
            <html>
            <head>
                <title>Non-Polish Text Extraction Results</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .no-content { text-align: center; color: #666; padding: 20px; }
                </style>
            </head>
            <body>
                <h1>Non-Polish Text Extraction Results</h1>
                <div class="no-content">
                    <p>No non-Polish text content found on this page.</p>
                </div>
            </body>
            </html>
            """
        
        table_rows = ""
        for i, (tag_name, language, text) in enumerate(elements, 1):
            # Escape HTML content for safe display
            escaped_text = html.escape(text)
            escaped_tag = html.escape(tag_name)
            escaped_lang = html.escape(language)
            
            table_rows += f"""
                <tr>
                    <td>{i}</td>
                    <td><code>&lt;{escaped_tag}&gt;</code></td>
                    <td><span class="lang-code">{escaped_lang}</span></td>
                    <td class="text-content">{escaped_text}</td>
                </tr>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Non-Polish Text Extraction Results</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .stats {{
                    background: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                    vertical-align: top;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                    position: sticky;
                    top: 0;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .lang-code {{
                    background: #007bff;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .text-content {{
                    max-width: 400px;
                    word-wrap: break-word;
                    line-height: 1.4;
                }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: monospace;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Non-Polish Text Extraction Results</h1>
                
                <div class="stats">
                    <strong>Found {len(elements)} non-Polish text snippet(s)</strong>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">#</th>
                            <th style="width: 100px;">HTML Tag</th>
                            <th style="width: 100px;">Language</th>
                            <th>Text Content</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>Generated by Web Page Non-Polish Text Extractor</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def process_url(self, url: str) -> str:
        """Main processing function."""
        # Validate URL
        if not self.validate_url(url):
            raise Exception("Invalid URL format")
        
        # Fetch page content
        print(f"Fetching content from: {url}")
        html_content = self.fetch_page(url)
        
        # Parse HTML
        print("Parsing HTML content...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text elements
        print("Extracting text from HTML elements...")
        text_elements = self.extract_text_elements(soup)
        print(f"Found {len(text_elements)} text elements")
        
        # Filter non-Polish content
        print("Detecting languages and filtering non-Polish content...")
        print("Using ultra-aggressive 8-layer Polish detection system...")
        non_polish_elements = self.filter_non_polish(text_elements) 
        polish_filtered = len(text_elements) - len(non_polish_elements)
        print(f"Filtered out {polish_filtered} Polish text snippets")
        print(f"Found {len(non_polish_elements)} non-Polish text snippets")
        
        # Generate HTML table
        print("Generating HTML table...")
        html_output = self.generate_html_table(non_polish_elements)
        
        return html_output


def get_url_input() -> str:
    """Get URL from command line argument or user input."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        try:
            return input("Enter the URL to analyze: ").strip()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)


def main():
    """Main function."""
    print("Web Page Non-Polish Text Extractor")
    print("=" * 40)
    
    try:
        # Get URL input
        url = get_url_input()
        
        if not url:
            print("Error: No URL provided")
            sys.exit(1)
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Create extractor and process URL
        extractor = WebTextExtractor()
        html_output = extractor.process_url(url)
        
        # Save output to file
        output_filename = "non_polish_text_results.html"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        print(f"\nResults saved to: {output_filename}")
        print("Open this file in a web browser to view the results.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
