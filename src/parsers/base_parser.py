from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseParser(ABC):
    """Abstract base class for all parsers"""
    
    @abstractmethod
    def parse_quotes_from_html(self, html: str) -> List[Dict[str, any]]:
        """Parse all quotes from HTML content"""
        pass
    
    @abstractmethod
    def has_next_page(self, html: str) -> bool:
        """Check if there is a next page"""
        pass
    
    @abstractmethod
    def extract_page_number(self, html: str) -> int:
        """Extract current page number from HTML"""
        pass
    
    @abstractmethod
    def has_no_quotes(self, html: str) -> bool:
        """Check if page contains 'No quotes found!' message"""
        pass

