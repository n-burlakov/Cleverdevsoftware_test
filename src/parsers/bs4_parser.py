import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from .base_parser import BaseParser


class BS4Parser(BaseParser):
    """Parser using BeautifulSoup library"""
    
    def parse_quotes_from_html(self, html: str) -> List[Dict[str, any]]:
        """Parsing all quotes from the page"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            quotes = []
            
            quote_elements = soup.find_all("div", class_="quote")
            
            for quote_element in quote_elements:
                try:
                    quote_data = self._parse_single_quote(quote_element)
                    if quote_data:
                        quotes.append(quote_data)
                except Exception:
                    continue
            
            return quotes
        except Exception:
            return []
    
    def _parse_single_quote(self, quote_element) -> Optional[Dict[str, any]]:
        """Parsing one quote"""
        try:
            text_element = quote_element.find("span", class_="text")
            author_element = quote_element.find("small", class_="author")
            tags_elements = quote_element.find_all("a", class_="tag")
            
            if not all([text_element, author_element]):
                return None
            
            quote_data = {
                "text": text_element.get_text(strip=True).strip('"'),
                "author": author_element.get_text(strip=True),
                "tags": [tag.get_text(strip=True) for tag in tags_elements]
            }
            
            return quote_data
            
        except Exception:
            return None
    
    def has_next_page(self, html: str) -> bool:
        """Check for the presence of the next page"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            next_button = soup.find("li", class_="next")
            return next_button is not None
        except Exception:
            return False
    
    def extract_page_number(self, html: str) -> int:
        """Extract the number of the current page"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            pagination = soup.find("ul", class_="pager")
            
            if pagination:
                current_page = pagination.find("span", class_="current")
                if current_page:
                    match = re.search(r"(\d+)", current_page.text)
                    if match:
                        return int(match.group(1))
            return 1
        except Exception:
            return 1
    
    def has_no_quotes(self, html: str) -> bool:
        """Check if page contains "No quotes found!" message"""
        try:
            return "No quotes found!" in html
        except Exception:
            return False
