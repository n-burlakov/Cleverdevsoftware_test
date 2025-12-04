import re

from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class QuoteParser:
    """Class for parsing quotes"""
    
    @staticmethod
    def parse_quotes_from_html(html: str) -> List[Dict[str, any]]:
        """Parsing all quotes from the page"""
        soup = BeautifulSoup(html, 'html.parser')
        quotes = []
        
        quote_elements = soup.find_all('div', class_='quote')
        
        for quote_element in quote_elements:
            try:
                quote_data = QuoteParser._parse_single_quote(quote_element)
                if quote_data:
                    quotes.append(quote_data)
            except Exception as e:
                continue
        
        return quotes
    
    @staticmethod
    def _parse_single_quote(quote_element) -> Optional[Dict[str, any]]:
        """Parsing one quote"""
        try:
            text_element = quote_element.find('span', class_='text')
            author_element = quote_element.find('small', class_='author')
            tags_elements = quote_element.find_all('a', class_='tag')
            
            if not all([text_element, author_element]):
                return None
            
            quote_data = {
                'text': text_element.get_text(strip=True).strip('"'),
                'author': author_element.get_text(strip=True),
                'tags': [tag.get_text(strip=True) for tag in tags_elements]
            }
            
            return quote_data
            
        except Exception:
            return None
    
    @staticmethod
    def has_next_page(html: str) -> bool:
        """Check for the presence of the next page"""
        soup = BeautifulSoup(html, 'html.parser')
        next_button = soup.find('li', class_='next')
        return next_button is not None
    
    @staticmethod
    def extract_page_number(html: str) -> int:
        """Extract the number of the current page"""
        soup = BeautifulSoup(html, 'html.parser')
        pagination = soup.find('ul', class_='pager')
        
        if pagination:
            current_page = pagination.find('span', class_='current')
            if current_page:
                match = re.search(r'(\d+)', current_page.text)
                if match:
                    return int(match.group(1))
        return 1
